window.addEventListener("load", function () {
    /*
    try {
        if (!navigator.geolocation) {
            console.log("Geolocation not supported");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            function (pos) {
                var lat = pos.coords.latitude;
                var lon = pos.coords.longitude;
                var newHash = "lat=" + lat + "&lon=" + lon;
                if (window.location.hash !== "#" + newHash) {
                    window.location.hash = newHash;
                }
            },
            function (err) {
                console.log("Geolocation error", err);
            },
            { timeout: 5000 }
        );
    } catch (e) {
        console.log("Error in geolocation script", e);
    }
    */
});
