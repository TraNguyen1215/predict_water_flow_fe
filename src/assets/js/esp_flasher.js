(function () {
  if (window.initializeEspFlasher) {
    return;
  }
  function formatError(error) {
    if (!error) {
      return "Không rõ nguyên nhân";
    }
    if (typeof error === "string") {
      return error;
    }
    if (error.message) {
      return error.message;
    }
    if (error.name) {
      return error.name;
    }
    try {
      return JSON.stringify(error);
    } catch (e) {
      return String(error);
    }
  }

  window.initializeEspFlasher = function () {
    const state = {
      port: null,
      transport: null,
      loader: null,
      firmware: null,
      firmwareName: "",
      isConnecting: false,
      isFlashing: false,
      shouldAutoFlash: true,
    };

    const maxAttempts = 80;
    let attempts = 0;

    function setupIfReady() {
      const root = document.getElementById("esp-flasher-root");
      if (!root) {
        return false;
      }

      const hasConnectBtn = root.querySelector("#esp-connect-btn");
      const hasDisconnectBtn = root.querySelector("#esp-disconnect-btn");
      const hasFlashBtn = root.querySelector("#esp-flash-btn");
      const uploadWrapper = root.querySelector("#esp-firmware-input");

      if (
        !hasConnectBtn ||
        !hasDisconnectBtn ||
        !hasFlashBtn ||
        !uploadWrapper
      ) {
        return false;
      }

      if (root.dataset.bound === "true") {
        return true;
      }

      const getConnectBtn = () => root.querySelector("#esp-connect-btn");
      const getDisconnectBtn = () => root.querySelector("#esp-disconnect-btn");
      const getFlashBtn = () => root.querySelector("#esp-flash-btn");
      const getFileInput = () =>
        root.querySelector("#esp-firmware-input input[type='file']");
      const getStatusEl = () => root.querySelector("#esp-status");
      const getProgressInner = () => root.querySelector("#esp-progress-inner");
      const getProgressLabel = () => root.querySelector("#esp-progress-label");
      const getLogEl = () => root.querySelector("#esp-log");
      const getSelectedLabel = () =>
        root.querySelector("#esp-firmware-selected");
      let currentEnvironmentWarning = "";

      function writeLog(message) {
        const logEl = getLogEl();
        if (!logEl) {
          return;
        }
        const time = new Date().toLocaleTimeString();
        logEl.textContent += `[${time}] ${message}\n`;
        logEl.scrollTop = logEl.scrollHeight;
      }

      function setStatus(message, variant) {
        const statusEl = getStatusEl();
        if (!statusEl) {
          return;
        }
        statusEl.textContent = message || "";
        statusEl.dataset.variant = variant || "info";
        statusEl.style.display = message ? "block" : "none";
      }

      function updateProgress(percent, label) {
        const safePercent = Math.max(0, Math.min(100, percent || 0));
        const progressInner = getProgressInner();
        if (progressInner) {
          progressInner.style.width = `${safePercent}%`;
        }
        const progressLabel = getProgressLabel();
        if (progressLabel) {
          progressLabel.textContent = label || `${safePercent.toFixed(0)}%`;
        }
      }

      function resetProgress() {
        updateProgress(0, "Chưa nạp");
      }

      function evaluateEnvironment() {
        const issues = [];
        if (!window.isSecureContext) {
          issues.push(
            "Trang cần chạy trong Secure Context (https:// hoặc http://localhost) để sử dụng Web Serial."
          );
        }

        const serial = navigator.serial;
        if (!serial) {
          issues.push(
            "Trình duyệt hiện không cung cấp Web Serial API. Hãy dùng Chrome/Edge mới nhất và bật Web Serial trong chrome://flags (Enable Experimental Web Platform features)."
          );
        } else if (typeof serial.requestPort !== "function") {
          issues.push(
            "navigator.serial.requestPort không khả dụng. Hãy kiểm tra lại quyền Web Serial trên trình duyệt."
          );
        }

        if (issues.length) {
          const combined = issues.join(" ");
          if (combined !== currentEnvironmentWarning) {
            currentEnvironmentWarning = combined;
            setStatus(combined, "danger");
          }
          return false;
        }

        if (currentEnvironmentWarning) {
          const statusEl = getStatusEl();
          if (statusEl && statusEl.textContent === currentEnvironmentWarning) {
            setStatus("", "info");
          }
          currentEnvironmentWarning = "";
        }

        return true;
      }

      function updateButtons() {
        const connectBtn = getConnectBtn();
        const disconnectBtn = getDisconnectBtn();
        const flashBtn = getFlashBtn();
        const fileInput = getFileInput();
        const envReady = evaluateEnvironment();

        if (connectBtn) {
          connectBtn.disabled =
            !envReady || !!state.port || state.isConnecting || state.isFlashing;
        }
        if (disconnectBtn) {
          disconnectBtn.disabled = !state.port || state.isFlashing;
        }
        if (flashBtn) {
          flashBtn.disabled =
            !state.port || !state.loader || !state.firmware || state.isFlashing;
        }
        if (fileInput) {
          fileInput.disabled = state.isFlashing;
        }
        if (uploadWrapper) {
          uploadWrapper.classList.toggle(
            "esp-upload-disabled",
            state.isFlashing
          );
        }
      }

      async function disconnectDevice(showMessage) {
        try {
          if (state.loader && typeof state.loader.disconnect === "function") {
            await state.loader.disconnect();
          }
        } catch (err) {
          writeLog(`Lỗi khi ngắt kết nối loader: ${formatError(err)}`);
        }
        try {
          if (
            state.transport &&
            typeof state.transport.disconnect === "function"
          ) {
            await state.transport.disconnect();
          }
        } catch (err) {
          writeLog(`Lỗi khi ngắt kết nối transport: ${formatError(err)}`);
        }
        try {
          if (state.port && typeof state.port.close === "function") {
            await state.port.close();
          }
        } catch (err) {
          writeLog(`Lỗi khi đóng cổng: ${formatError(err)}`);
        }

        state.port = null;
        state.transport = null;
        state.loader = null;

        if (showMessage) {
          setStatus("Đã ngắt kết nối thiết bị.", "info");
        }
        updateButtons();
      }

      async function connectDevice() {
        if (state.isConnecting || state.port) {
          return;
        }

        if (
          !navigator.serial ||
          typeof navigator.serial.requestPort !== "function"
        ) {
          setStatus(
            "Trình duyệt không hỗ trợ hoặc chưa bật Web Serial API. Hãy dùng Chrome/Edge mới và bật flag 'Experimental Web Platform features' (chrome://flags/#enable-experimental-web-platform-features).",
            "danger"
          );
          console.warn("navigator.serial hiện tại:", navigator.serial);
          return;
        } // Wait for esptool-js library to load

        state.isConnecting = true;
        updateButtons();
        setStatus("Đang yêu cầu quyền truy cập cổng Serial...", "info");

        try {
          const port = await navigator.serial.requestPort();
          await port.open({ baudRate: 115200 });

          const Transport = window.Transport || window.esptool?.Transport;
          const ESPLoader = window.ESPLoader || window.esptool?.ESPLoader;

          state.port = port;
          state.transport = new Transport(port);

          const logger = (msg) => {
            if (msg) {
              writeLog(String(msg));
            }
          };

          state.loader = await ESPLoader.load(state.transport, {
            baudrate: 921600,
            debug: false,
            logger,
          });

          try {
            await state.loader.flashId();
          } catch (probeErr) {
            writeLog(`Không đọc được flash ID: ${formatError(probeErr)}`);
          }

          const chipName =
            state.loader.chipName ||
            (state.loader.chip &&
              (state.loader.chip.CHIP_NAME || state.loader.chip.name)) ||
            "ESP";
          setStatus(`Đã kết nối với ${chipName}.`, "success");
          writeLog("Thiết bị đã sẵn sàng.");
          updateButtons(); // Auto-flash if firmware is loaded and shouldAutoFlash is true

          if (
            state.firmware &&
            state.firmware.length > 0 &&
            state.shouldAutoFlash
          ) {
            writeLog("Bắt đầu nạp firmware tự động...");
            state.shouldAutoFlash = false; // Prevent multiple auto-flash attempts
            setTimeout(() => {
              flashFirmware();
            }, 500);
          }
        } catch (err) {
          const errorMessage = formatError(err);
          writeLog(`Không thể kết nối: ${errorMessage}`);
          if (err && err.name === "NotFoundError") {
            setStatus("Bạn đã huỷ chọn thiết bị.", "warning");
          } else if (err && err.name === "SecurityError") {
            setStatus(
              "Trình duyệt từ chối Web Serial vì trang chưa chạy trong Secure Context hoặc quyền bị chặn.",
              "danger"
            );
          } else {
            setStatus(`Không thể kết nối: ${errorMessage}`, "danger");
          }
          await disconnectDevice(false);
        } finally {
          state.isConnecting = false;
          updateButtons();
        }
      }

      async function loadFirmwareFromAssets(binFileName) {
        try {
          writeLog(`Đang tải firmware từ assets: ${binFileName}...`);
          setStatus("Đang tải firmware từ assets...", "info");

          const response = await fetch(`/assets/${binFileName}`);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const arrayBuffer = await response.arrayBuffer();
          state.firmware = new Uint8Array(arrayBuffer);
          state.firmwareName = binFileName;

          writeLog(
            `Đã tải firmware: ${binFileName} (${state.firmware.length} byte).`
          );
          setStatus(
            'Firmware đã sẵn sàng. Kết nối thiết bị rồi bấm "Bắt đầu nạp".',
            "info"
          );
          resetProgress();
          updateButtons();

          const selectedLabel = getSelectedLabel();
          if (selectedLabel) {
            selectedLabel.textContent = `Đã tải: ${binFileName}`;
          }
        } catch (err) {
          const errorMessage = formatError(err);
          state.firmware = null;
          state.firmwareName = "";
          setStatus(
            `Không thể tải firmware từ assets: ${errorMessage}`,
            "danger"
          );
          writeLog(`Không thể tải firmware từ assets: ${errorMessage}`);
          updateButtons();

          const selectedLabel = getSelectedLabel();
          if (selectedLabel) {
            selectedLabel.textContent = "";
          }
        }
      }

      function handleFileSelected(event) {
        const files = event.target.files || [];
        const inputElement = event.target;
        if (!files.length) {
          state.firmware = null;
          state.firmwareName = "";
          resetProgress();
          updateButtons();
          const selectedLabel = getSelectedLabel();
          if (selectedLabel) {
            selectedLabel.textContent = "";
          }
          return;
        }

        const file = files[0];
        const reader = new FileReader();
        reader.onload = function (loadEvent) {
          const arrayBuffer = loadEvent.target.result;
          state.firmware = new Uint8Array(arrayBuffer);
          state.firmwareName = file.name;
          writeLog(
            `Đã chọn firmware: ${file.name} (${state.firmware.length} byte).`
          );
          setStatus(
            'Firmware đã sẵn sàng. Kết nối thiết bị rồi bấm "Bắt đầu nạp".',
            "info"
          );
          resetProgress();
          updateButtons();
          const selectedLabel = getSelectedLabel();
          if (selectedLabel) {
            selectedLabel.textContent = `Đã chọn: ${file.name}`;
          }
          if (inputElement && typeof inputElement.value === "string") {
            inputElement.value = "";
          }
        };
        reader.onerror = function () {
          state.firmware = null;
          state.firmwareName = "";
          setStatus("Không thể đọc tệp firmware.", "danger");
          writeLog("Không thể đọc tệp firmware.");
          updateButtons();
          const selectedLabel = getSelectedLabel();
          if (selectedLabel) {
            selectedLabel.textContent = "";
          }
          if (inputElement && typeof inputElement.value === "string") {
            inputElement.value = "";
          }
        };
        reader.readAsArrayBuffer(file);
      }

      function parseAddress(rawAddress) {
        if (!rawAddress) {
          return 0x1000;
        }
        const trimmed = rawAddress.trim();
        if (!trimmed) {
          return 0x1000;
        }
        const asNumber = Number(trimmed);
        if (!Number.isNaN(asNumber) && asNumber >= 0) {
          return Math.floor(asNumber);
        }
        const parsedHex = Number.parseInt(trimmed, 16);
        if (!Number.isNaN(parsedHex) && parsedHex >= 0) {
          return parsedHex;
        }
        return 0x1000;
      }

      async function flashFirmware() {
        if (!state.loader || !state.port) {
          setStatus("Chưa kết nối với thiết bị.", "danger");
          return;
        }
        if (!state.firmware) {
          setStatus("Bạn chưa chọn tệp firmware (.bin).", "danger");
          return;
        }

        const addressInput = root.querySelector("#esp-start-address");
        const eraseCheckbox = root.querySelector("#esp-erase-checkbox");
        const addressValue = parseAddress(addressInput && addressInput.value);
        const eraseAll = !!(eraseCheckbox && eraseCheckbox.checked);

        state.isFlashing = true;
        updateButtons();
        setStatus("Đang nạp firmware lên thiết bị...", "info");
        writeLog(
          `Bắt đầu nạp firmware tới địa chỉ 0x${addressValue.toString(
            16
          )} (xóa toàn bộ: ${eraseAll ? "Có" : "Không"}).`
        );
        updateProgress(0, "Bắt đầu...");

        try {
          if (typeof state.loader.writeFlash !== "function") {
            throw new Error("Phiên bản esptool-js không hỗ trợ writeFlash.");
          }

          const fileEntry = {
            data: state.firmware,
            address: addressValue,
            fileName: state.firmwareName || "firmware.bin",
          };

          const flashOptions = {
            flashSize: "keep",
            eraseAll,
            compress: true,
            calculateMD5Hash: true,
            progressCallback: function (fileIndex, bytesWritten, totalBytes) {
              const percent = totalBytes
                ? (bytesWritten / totalBytes) * 100
                : 0;
              updateProgress(
                percent,
                `${fileEntry.fileName}: ${bytesWritten}/${totalBytes} byte`
              );
            },
          };

          await state.loader.writeFlash([fileEntry], flashOptions);

          try {
            if (typeof state.loader.reset === "function") {
              await state.loader.reset();
            } else if (
              state.transport &&
              typeof state.transport.sendReset === "function"
            ) {
              await state.transport.sendReset();
            }
          } catch (resetErr) {
            writeLog(
              `Không thể khởi động lại thiết bị tự động: ${formatError(
                resetErr
              )}`
            );
          }

          setStatus(
            "Nạp firmware thành công! Bạn có thể khởi động lại thiết bị.",
            "success"
          );
          writeLog("Hoàn tất nạp firmware.");
        } catch (err) {
          const message = formatError(err);
          setStatus(`Nạp firmware thất bại: ${message}`, "danger");
          writeLog(`Nạp firmware thất bại: ${message}`);
        } finally {
          state.isFlashing = false;
          updateButtons();
        }
      }

      async function handleDisconnectClick() {
        await disconnectDevice(true);
      }

      function handleRootClick(event) {
        const target = event.target;
        if (target.closest && target.closest("#esp-connect-btn")) {
          event.preventDefault();
          connectDevice();
          return;
        }
        if (target.closest && target.closest("#esp-disconnect-btn")) {
          event.preventDefault();
          handleDisconnectClick();
          return;
        }
        if (target.closest && target.closest("#esp-load-from-assets-btn")) {
          event.preventDefault();
          loadFirmwareFromAssets("sketch_oct15a.ino.bin");
          return;
        }
        if (target.closest && target.closest("#esp-flash-btn")) {
          event.preventDefault();
          flashFirmware();
        }
      }

      function handleRootChange(event) {
        const target = event.target;
        if (
          target &&
          target.matches("input[type='file']") &&
          target.closest("#esp-firmware-input")
        ) {
          handleFileSelected(event);
        }
      } // Add DOMNodeInserted listener to detect when dcc.Upload creates input element

      if (uploadWrapper) {
        uploadWrapper.addEventListener(
          "DOMNodeInserted",
          function checkForFileInput() {
            const fileInput = uploadWrapper.querySelector("input[type='file']");
            if (fileInput && !fileInput.__changeListenerAttached) {
              fileInput.__changeListenerAttached = true;
              fileInput.addEventListener("change", handleFileSelected);
            }
          },
          true
        ); // Check immediately in case input already exists

        setTimeout(function () {
          const fileInput = uploadWrapper.querySelector("input[type='file']");
          if (fileInput && !fileInput.__changeListenerAttached) {
            fileInput.__changeListenerAttached = true;
            fileInput.addEventListener("change", handleFileSelected);
          }
        }, 100);
      }

      root.addEventListener("click", handleRootClick);
      root.addEventListener("change", handleRootChange);

      root.dataset.bound = "true";
      updateButtons();
      resetProgress();
      if (!currentEnvironmentWarning) {
        setStatus("", "info");
      }
      const initialLog = getLogEl();
      if (initialLog) {
        initialLog.textContent = "";
      } // Auto-load firmware from assets and auto-connect on initialization

      const autoInitialize = async () => {
        // Wait for esptool-js library to load
        let libWaitAttempts = 0;
        while (!window.esptool && libWaitAttempts < 100) {
          await new Promise((resolve) => setTimeout(resolve, 100));
          libWaitAttempts++;
        }

        if (!window.esptool) {
          writeLog("Lỗi: Không thể tải thư viện esptool-js.");
          setStatus(
            "Không thể tải thư viện esptool-js. Vui lòng tải lại trang.",
            "danger"
          );
          return;
        }

        try {
          writeLog("Đang tải firmware từ assets tự động...");
          await loadFirmwareFromAssets("sketch_oct15a.ino.bin"); // Auto-connect after firmware is loaded

          writeLog("Đang kết nối thiết bị tự động...");
          await connectDevice();
        } catch (err) {
          writeLog(`Lỗi khi khởi tạo: ${formatError(err)}`);
        }
      };

      setTimeout(autoInitialize, 500);

      if (
        navigator.serial &&
        typeof navigator.serial.addEventListener === "function" &&
        !navigator.serial.__espFlasherBound
      ) {
        navigator.serial.__espFlasherBound = true;
        navigator.serial.addEventListener("connect", () => {
          writeLog("Trình duyệt phát hiện thiết bị Serial mới.");
          if (!state.port && !state.isConnecting) {
            setStatus(
              'Đã phát hiện thiết bị Serial mới. Nhấn "Kết nối thiết bị" để chọn.',
              "info"
            );
            updateButtons();
          }
        });
        navigator.serial.addEventListener("disconnect", (event) => {
          writeLog("Một thiết bị Serial đã ngắt kết nối.");
          if (state.port && event && event.target === state.port) {
            disconnectDevice(false).catch(() => {});
            setStatus(
              "Thiết bị đang sử dụng đã bị ngắt kết nối. Vui lòng kiểm tra lại cáp và kết nối lại.",
              "warning"
            );
          }
          updateButtons();
        });
      }

      const cleanup = () => {
        root.removeEventListener("click", handleRootClick);
        root.removeEventListener("change", handleRootChange);
      };

      window.addEventListener(
        "beforeunload",
        () => {
          if (state.port) {
            disconnectDevice(false).catch(() => {});
          }
          cleanup();
        },
        { once: true }
      );

      root.addEventListener("dash:unmount", cleanup, { once: true });

      return true;
    }

    function trySetup() {
      if (setupIfReady()) {
        return;
      }
      attempts += 1;
      if (attempts < maxAttempts) {
        setTimeout(trySetup, 200);
      }
    }

    trySetup();
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  if (typeof window.initializeEspFlasher === "function") {
    window.initializeEspFlasher();
  } else {
    console.error("initializeEspFlasher chưa được định nghĩa!");
  }
});
