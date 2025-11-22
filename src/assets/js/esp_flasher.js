(function () {
  if (window.initializeEspFlasher) {
    return;
  }

  function formatError(error) {
    if (!error) return "Không rõ nguyên nhân";
    if (typeof error === "string") return error;
    if (error.message) return error.message;
    if (error.name) return error.name;
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
      if (!root) return false;

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

      if (root.dataset.bound === "true") return true;

      // Selectors
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
        if (!logEl) return;
        const time = new Date().toLocaleTimeString();
        logEl.textContent += `[${time}] ${message}\n`;
        logEl.scrollTop = logEl.scrollHeight;
      }

      function setStatus(message, variant) {
        const statusEl = getStatusEl();
        if (!statusEl) return;
        statusEl.textContent = message || "";
        statusEl.dataset.variant = variant || "info";
        statusEl.style.display = message ? "block" : "none";
      }

      function updateProgress(percent, label) {
        const safePercent = Math.max(0, Math.min(100, percent || 0));
        const progressInner = getProgressInner();
        if (progressInner) progressInner.style.width = `${safePercent}%`;
        const progressLabel = getProgressLabel();
        if (progressLabel)
          progressLabel.textContent = label || `${safePercent.toFixed(0)}%`;
      }

      function resetProgress() {
        updateProgress(0, "Chưa nạp");
      }

      function evaluateEnvironment() {
        const issues = [];
        if (!window.isSecureContext) {
          issues.push(
            "Trang cần chạy trong Secure Context (https:// hoặc http://localhost)."
          );
        }
        const serial = navigator.serial;
        if (!serial) {
          issues.push(
            "Trình duyệt không hỗ trợ Web Serial API (Dùng Chrome/Edge mới nhất)."
          );
        } else if (typeof serial.requestPort !== "function") {
          issues.push("navigator.serial.requestPort không khả dụng.");
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
          setStatus("", "info");
          currentEnvironmentWarning = "";
        }
        return true;
      }

      function updateButtons() {
        const connectBtn = getConnectBtn();
        const disconnectBtn = getDisconnectBtn();
        const flashBtn = getFlashBtn();
        const eraseBtn = root.querySelector("#esp-erase-checkbox");
        const fileInput = getFileInput();
        const envReady = evaluateEnvironment();

        if (connectBtn)
          connectBtn.disabled =
            !envReady || !!state.port || state.isConnecting || state.isFlashing;
        if (disconnectBtn)
          disconnectBtn.disabled = !state.port || state.isFlashing;
        if (flashBtn)
          flashBtn.disabled =
            !state.port || !state.loader || !state.firmware || state.isFlashing;
        if (fileInput) fileInput.disabled = state.isFlashing;
        if (eraseBtn) eraseBtn.disabled = state.isFlashing || !state.port;
        if (uploadWrapper)
          uploadWrapper.classList.toggle(
            "esp-upload-disabled",
            state.isFlashing
          );
      }

      // --- HELPER ĐỂ LẤY CLASS TỪ THƯ VIỆN ---
      function getEspClasses() {
        // Xử lý trường hợp module export default hoặc named export
        const lib = window.esptool?.default || window.esptool || window;
        const Transport = lib.Transport || window.Transport;
        const ESPLoader = lib.ESPLoader || window.ESPLoader;
        return { Transport, ESPLoader };
      }

      async function disconnectDevice(showMessage) {
        try {
          if (state.loader && typeof state.loader.disconnect === "function")
            await state.loader.disconnect();
        } catch (err) {} // Ignore loader disconnect error

        try {
          if (
            state.transport &&
            typeof state.transport.disconnect === "function"
          )
            await state.transport.disconnect();
        } catch (err) {}

        try {
          if (state.port && typeof state.port.close === "function")
            await state.port.close();
        } catch (err) {
          writeLog(`Lỗi khi đóng cổng: ${formatError(err)}`);
        }

        state.port = null;
        state.transport = null;
        state.loader = null;

        if (showMessage) setStatus("Đã ngắt kết nối thiết bị.", "info");
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
          setStatus("Trình duyệt không hỗ trợ Web Serial.", "danger");
          return;
        }

        state.isConnecting = true;
        updateButtons();
        setStatus("Đang kết nối...", "info");

        try {
          const port = await navigator.serial.requestPort();
          // Mở port với tốc độ thấp nhất để đảm bảo ổn định
          await port.open({ baudRate: 115200 });

          const Transport = window.Transport || window.esptool?.Transport;
          const ESPLoader = window.ESPLoader || window.esptool?.ESPLoader;

          state.port = port;
          state.transport = new Transport(port);

          const terminalWrapper = {
            clean: () => {},
            writeLine: (data) => writeLog(data),
            write: (data) => writeLog(data),
          };

          // --- FIX MẠNH: CHUỖI RESET THỦ CÔNG (HARD RESET) ---
          // Giúp mạch vào chế độ Bootloader trước khi thư viện chạy
          writeLog("Đang gửi tín hiệu Reset vào Bootloader...");
          try {
            await state.transport.setDTR(false);
            await state.transport.setRTS(false);
            await new Promise((resolve) => setTimeout(resolve, 100));

            // Bước 1: Kéo GPIO0 xuống thấp (DTR=true) và Reset xuống thấp (RTS=true)
            await state.transport.setDTR(true);
            await state.transport.setRTS(true);
            await new Promise((resolve) => setTimeout(resolve, 100));

            // Bước 2: Nhả Reset (RTS=false) để chip khởi động, vẫn giữ GPIO0 thấp
            await state.transport.setRTS(false);

            // Bước 3: Đợi một chút để chip nhận diện chế độ boot
            await new Promise((resolve) => setTimeout(resolve, 400));

            // Bước 4: Nhả GPIO0 (DTR=false)
            await state.transport.setDTR(false);
          } catch (e) {
            console.warn("Lỗi khi gửi tín hiệu reset:", e);
          }
          // ---------------------------------------------------

          // Khởi tạo loader ở tốc độ 115200 (quan trọng)
          state.loader = new ESPLoader(
            state.transport,
            115200,
            terminalWrapper
          );

          try {
            // Thử kết nối. mode: 'default_reset' giúp thử lại các cách reset khác nếu cách trên thất bại
            const espRunner = await state.loader.main_fn({
              mode: "default_reset",
            });

            // Kiểm tra kỹ xem chip đã được detect chưa
            if (!state.loader.chip || !state.loader.chip.CHIP_NAME) {
              // Nếu main_fn chạy qua mà không detect được chip, ta gọi flashId để ép check
              await state.loader.flashId();
            }
          } catch (probeErr) {
            writeLog(`Lỗi nhận diện chip: ${formatError(probeErr)}`);
            throw new Error(
              "Không nhận diện được Chip. Hãy giữ nút BOOT trên mạch rồi thử lại."
            );
          }

          const chipName = state.loader.chipName || "ESP Device";
          setStatus(`Đã kết nối: ${chipName}`, "success");
          writeLog(`Thành công! Chip: ${chipName}`);
          updateButtons();

          if (
            state.firmware &&
            state.firmware.length > 0 &&
            state.shouldAutoFlash
          ) {
            writeLog("Tự động nạp sau 1s...");
            state.shouldAutoFlash = false;
            setTimeout(() => {
              flashFirmware();
            }, 1000);
          }
        } catch (err) {
          const errorMessage = formatError(err);
          writeLog(`Thất bại: ${errorMessage}`);

          if (
            errorMessage.includes("Boot") ||
            errorMessage.includes("Timed out")
          ) {
            setStatus(
              "Lỗi: Hãy giữ nút BOOT trên mạch khi bấm Kết nối!",
              "danger"
            );
          } else {
            setStatus(`Lỗi kết nối: ${errorMessage}`, "danger");
          }

          // Dọn dẹp
          state.port = null;
          state.loader = null;
          if (state.transport) {
            try {
              await state.transport.disconnect();
            } catch (e) {}
          }
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
          if (!response.ok)
            throw new Error(`HTTP error! status: ${response.status}`);

          const arrayBuffer = await response.arrayBuffer();
          state.firmware = new Uint8Array(arrayBuffer);
          state.firmwareName = binFileName;

          writeLog(
            `Đã tải firmware: ${binFileName} (${state.firmware.length} byte).`
          );
          setStatus(
            'Firmware đã sẵn sàng. Vui lòng bấm "Kết nối thiết bị" để bắt đầu.',
            "info"
          );

          resetProgress();
          updateButtons();
          const selectedLabel = getSelectedLabel();
          if (selectedLabel)
            selectedLabel.textContent = `Đã tải: ${binFileName}`;
        } catch (err) {
          const msg = formatError(err);
          state.firmware = null;
          setStatus(`Không thể tải firmware: ${msg}`, "danger");
          writeLog(`Lỗi tải firmware: ${msg}`);
          updateButtons();
        }
      }

      function handleFileSelected(event) {
        const files = event.target.files || [];
        if (!files.length) return;
        const file = files[0];
        const reader = new FileReader();
        reader.onload = function (loadEvent) {
          state.firmware = new Uint8Array(loadEvent.target.result);
          state.firmwareName = file.name;
          writeLog(`Đã chọn firmware: ${file.name}`);
          setStatus(
            'Firmware đã sẵn sàng. Kết nối thiết bị rồi bấm "Bắt đầu nạp".',
            "info"
          );
          resetProgress();
          updateButtons();
          const lbl = getSelectedLabel();
          if (lbl) lbl.textContent = `Đã chọn: ${file.name}`;
        };
        reader.readAsArrayBuffer(file);
        event.target.value = "";
      }

      function parseAddress(rawAddress) {
        if (!rawAddress) return 0x1000;
        const trimmed = rawAddress.trim();
        const asNumber = Number(trimmed);
        if (!Number.isNaN(asNumber) && asNumber >= 0)
          return Math.floor(asNumber);
        const parsedHex = parseInt(trimmed, 16);
        return !Number.isNaN(parsedHex) && parsedHex >= 0 ? parsedHex : 0x1000;
      }

      async function flashFirmware() {
        if (!state.loader || !state.port) {
          setStatus("Chưa kết nối với thiết bị.", "danger");
          return;
        }
        if (!state.firmware) {
          setStatus("Chưa có firmware.", "danger");
          return;
        }

        const addressInput = root.querySelector("#esp-start-address");
        const eraseEl = root.querySelector("#esp-erase-checkbox");
        const addressValue = parseAddress(addressInput && addressInput.value);

        let eraseAll = false;
        try {
          if (eraseEl) {
            eraseAll =
              typeof eraseEl.checked !== "undefined"
                ? !!eraseEl.checked
                : eraseEl.classList.contains("active");
          }
        } catch (e) {
          eraseAll = false;
        }

        state.isFlashing = true;
        updateButtons();
        setStatus("Đang nạp firmware...", "info");
        writeLog(
          `Bắt đầu nạp tại 0x${addressValue.toString(
            16
          )} (Xóa flash: ${eraseAll}).`
        );
        updateProgress(0, "Đang chuẩn bị...");

        try {
          const fileEntry = {
            data: state.firmware,
            address: addressValue,
            fileName: state.firmwareName || "firmware.bin",
          };

          const flashOptions = {
            fileArray: [fileEntry],
            flashSize: "keep",
            eraseAll,
            compress: true,
            calculateMD5Hash: true,
            reportProgress: function (fileIndex, bytesWritten, totalBytes) {
              const percent = totalBytes
                ? (bytesWritten / totalBytes) * 100
                : 0;
              updateProgress(percent, `Đang nạp: ${Math.floor(percent)}%`);
            },
          };

          await state.loader.writeFlash([fileEntry], flashOptions);

          try {
            if (typeof state.loader.hardReset === "function")
              await state.loader.hardReset();
            else if (typeof state.loader.reset === "function")
              await state.loader.reset();
          } catch (e) {
            writeLog("Không thể reset tự động.");
          }

          setStatus("Nạp thành công! Thiết bị đang khởi động lại.", "success");
          writeLog("Hoàn tất.");
        } catch (err) {
          const msg = formatError(err);
          setStatus(`Nạp thất bại: ${msg}`, "danger");
          writeLog(`Lỗi: ${msg}`);
        } finally {
          state.isFlashing = false;
          updateButtons();
        }
      }

      async function eraseFlashNow() {
        if (!state.loader || !state.port) return;
        if (state.isFlashing) return;

        state.isFlashing = true;
        updateButtons();
        setStatus("Đang xóa flash... (vui lòng chờ)", "info");
        writeLog("Bắt đầu xóa flash...");

        try {
          if (typeof state.loader.eraseFlash === "function")
            await state.loader.eraseFlash();
          else {
            await state.loader.runStub();
            await state.loader.eraseFlash();
          }
          setStatus("Xóa flash thành công.", "success");
          writeLog("Xóa flash hoàn tất.");
        } catch (err) {
          setStatus(`Xóa lỗi: ${formatError(err)}`, "danger");
        } finally {
          state.isFlashing = false;
          updateButtons();
        }
      }

      function handleRootClick(event) {
        const target = event.target;
        if (target.closest("#esp-connect-btn")) {
          event.preventDefault();
          connectDevice();
          return;
        }
        if (target.closest("#esp-disconnect-btn")) {
          event.preventDefault();
          disconnectDevice(true);
          return;
        }
        if (target.closest("#esp-flash-btn")) {
          event.preventDefault();
          flashFirmware();
          return;
        }
        // Nút Load assets (nếu có)
        if (target.closest("#esp-load-from-assets-btn")) {
          event.preventDefault();
          loadFirmwareFromAssets("sketch_oct15a.ino.bin");
          return;
        }
      }

      function handleRootChange(event) {
        if (
          event.target.matches("input[type='file']") &&
          event.target.closest("#esp-firmware-input")
        ) {
          handleFileSelected(event);
        }
      }

      if (uploadWrapper) {
        uploadWrapper.addEventListener("DOMNodeInserted", () => {
          const input = uploadWrapper.querySelector("input[type='file']");
          if (input && !input.__bound) {
            input.__bound = true;
            input.addEventListener("change", handleFileSelected);
          }
        });
      }

      root.addEventListener("click", handleRootClick);
      root.addEventListener("change", handleRootChange);
      root.dataset.bound = "true";
      updateButtons();

      const logEl = getLogEl();
      if (logEl) logEl.textContent = "";

      // --- LOGIC KHỞI TẠO TỰ ĐỘNG ---
      const autoInitialize = async () => {
        // 1. Tự động tải thư viện esptool-js từ CDN nếu chưa có
        if (!window.esptool) {
          writeLog("Đang tải thư viện esptool-js từ CDN...");
          try {
            // Dùng phiên bản bundle.js để đảm bảo tương thích
            const mod = await import(
              "https://unpkg.com/esptool-js@0.5.4/bundle.js"
            );
            window.esptool = mod;
            writeLog("Đã tải thư viện esptool-js.");
          } catch (e) {
            writeLog(`Lỗi tải thư viện: ${formatError(e)}`);
            setStatus(
              "Không tải được thư viện esptool-js. Kiểm tra internet.",
              "danger"
            );
            return;
          }
        }

        // 2. Tự động tải firmware từ assets
        try {
          writeLog("Tự động tải firmware mặc định...");
          await loadFirmwareFromAssets("sketch_oct15a.ino.bin");
          // 3. KHÔNG gọi connectDevice() ở đây để tránh lỗi User Gesture
          state.shouldAutoFlash = true; // Đặt cờ để khi user bấm kết nối thì sẽ nạp luôn
        } catch (e) {
          writeLog(`Lỗi khởi tạo: ${formatError(e)}`);
        }
      };

      // Chạy khởi tạo sau 500ms
      setTimeout(autoInitialize, 500);

      // Event listener cho Serial
      if (navigator.serial) {
        navigator.serial.addEventListener("disconnect", (e) => {
          if (state.port && e.target === state.port) {
            disconnectDevice(false);
            setStatus("Thiết bị đã ngắt kết nối.", "warning");
          }
        });
      }

      const cleanup = () => {
        root.removeEventListener("click", handleRootClick);
        root.removeEventListener("change", handleRootChange);
      };

      root.addEventListener("dash:unmount", cleanup, { once: true });
      return true;
    }

    function trySetup() {
      if (!setupIfReady()) {
        attempts++;
        if (attempts < maxAttempts) setTimeout(trySetup, 200);
      }
    }

    trySetup();
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  if (typeof window.initializeEspFlasher === "function") {
    window.initializeEspFlasher();
  }
});
