const API_BASE = "https://heatwave-early-warning-system.onrender.com";

let LATITUDE = 16.5062;
let LONGITUDE = 80.6480;
let CURRENT_LOCATION = "Vijayawada, India";


/* =====================================================
   BACKEND STATUS
===================================================== */

async function checkBackend() {

    try {

        const response = await fetch(
            `${API_BASE}/health`
        );

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        const data = await response.json();

        document.getElementById("systemStatus").textContent =
            `Backend: ${data.status}`;

    } catch (error) {

        console.error("Backend error:", error);

        document.getElementById("systemStatus").textContent =
            "Backend: Offline";
    }
}


/* =====================================================
   ML MODEL STATUS
===================================================== */

async function checkModel() {

    try {

        const response = await fetch(
            `${API_BASE}/api/risk/model-status`
        );

        if (!response.ok) {
            throw new Error("Model status unavailable");
        }

        const data = await response.json();

        const modelStatus =
            document.getElementById("modelStatus");

        if (data.model_ready === true) {

            modelStatus.innerHTML = `
                <strong style="color:#16a34a;">
                    ✅ Model Ready
                </strong>

                <br>

                <span>
                    ML model is loaded and ready for inference.
                </span>
            `;

        } else {

            modelStatus.innerHTML = `
                <strong>
                    ⚠️ Model Not Ready
                </strong>

                <br>

                <span>
                    ML model is currently unavailable.
                </span>
            `;
        }

    } catch (error) {

        console.error("Model error:", error);

        document.getElementById("modelStatus").innerHTML =
            "ML model status unavailable";
    }
}


/* =====================================================
   LOCATION SEARCH
===================================================== */

async function searchLocation() {

    const input =
        document.getElementById("locationInput");

    const status =
        document.getElementById("locationStatus");

    const button =
        document.getElementById("searchLocationButton");

    const locationName =
        input.value.trim();

    if (!locationName) {

        status.textContent =
            "Please enter a city or location.";

        return;
    }

    try {

        button.disabled = true;

        button.textContent =
            "Searching...";

        status.textContent =
            "Finding location...";


        /* Open-Meteo Geocoding API */

        const response =
            await fetch(
                `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(locationName)}&count=1&language=en&format=json`
            );


        if (!response.ok) {

            throw new Error(
                "Location search failed"
            );
        }


        const data =
            await response.json();


        if (
            !data.results ||
            data.results.length === 0
        ) {

            status.textContent =
                "Location not found. Try another city.";

            return;
        }


        const location =
            data.results[0];


        /* Update coordinates */

        LATITUDE =
            Number(location.latitude);

        LONGITUDE =
            Number(location.longitude);


        /* Build readable location name */

        CURRENT_LOCATION =
            location.name +
            (
                location.country
                    ? `, ${location.country}`
                    : ""
            );


        /* Update dashboard location */

        const locationElement =
            document.getElementById(
                "currentLocation"
            );

        if (locationElement) {

            locationElement.textContent =
                `📍 ${CURRENT_LOCATION}`;
        }


        status.textContent =
            `Location selected: ${CURRENT_LOCATION}`;


        /* Reload location-based data */

        await Promise.all([
           loadWeather()
           loadTemperatureForecast()
           loadAlerts()
       ]);


    } catch (error) {

        console.error(
            "Location search error:",
            error
        );

        status.textContent =
            "Unable to find this location. Please try again.";

    } finally {

        button.disabled = false;

        button.textContent =
            "🔍 Search";
    }
}


/* ENTER KEY FOR LOCATION SEARCH */

document
    .getElementById("locationInput")
    ?.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                searchLocation();
            }
        }
    );


/* =====================================================
   CURRENT WEATHER
===================================================== */

async function loadWeather() {

    try {

        const response = await fetch(
            `${API_BASE}/api/weather/current?lat=${LATITUDE}&lon=${LONGITUDE}`
        );

        if (!response.ok) {
            throw new Error("Weather API unavailable");
        }

        const data = await response.json();

        console.log(
            "Weather API response:",
            data
        );


        /* LAST UPDATED */

        const lastUpdated =
            document.getElementById(
                "lastUpdated"
            );

        if (lastUpdated) {

            lastUpdated.textContent =
                new Date().toLocaleString(
                    "en-IN",
                    {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                        hour12: true
                    }
                );
        }


        const stress =
            data.thermal_stress || {};


        /* BASIC WEATHER */

        document.getElementById(
            "temperature"
        ).textContent =
            data.temperature_c ?? "--";

        document.getElementById(
            "humidity"
        ).textContent =
            data.relative_humidity ?? "--";


        /* THERMAL STRESS */

        document.getElementById(
            "heatIndex"
        ).textContent =
            stress.heat_index_c ??
            data.heat_index_c ??
            "--";

        document.getElementById(
            "wetBulb"
        ).textContent =
            stress.wet_bulb_temperature_c ??
            data.wet_bulb_temperature_c ??
            "--";

        document.getElementById(
            "wbgt"
        ).textContent =
            stress.wbgt_c ??
            data.wbgt_c ??
            "--";


        /* HEAT RISK */

        const riskScore =
            stress.risk_score ??
            data.risk_score;

        const riskLevel =
            stress.risk_level ??
            data.risk_level;

        const riskCategory =
            stress.thermal_category ??
            data.thermal_category;


        document.getElementById(
            "riskScore"
        ).textContent =
            riskScore ?? "--";

        document.getElementById(
            "riskLevel"
        ).textContent =
            riskLevel ?? "--";

        document.getElementById(
            "riskCategory"
        ).textContent =
            riskCategory ?? "--";


        /* =================================================
           HEAT RISK METER
        ================================================= */

        const riskMeterFill =
            document.getElementById(
                "riskMeterFill"
            );

        if (
            riskMeterFill &&
            riskScore !== undefined &&
            riskScore !== null
        ) {

            const score =
                Math.max(
                    0,
                    Math.min(
                        100,
                        Number(riskScore)
                    )
                );


            riskMeterFill.style.width =
                `${score}%`;


            const level =
                String(
                    riskLevel || ""
                ).toLowerCase();


            if (
                level.includes("extreme")
            ) {

                riskMeterFill.style.background =
                    "#dc2626";

            } else if (
                level.includes("high")
            ) {

                riskMeterFill.style.background =
                    "#ea580c";

            } else if (
                level.includes("moderate")
            ) {

                riskMeterFill.style.background =
                    "#f59e0b";

            } else {

                riskMeterFill.style.background =
                    "#16a34a";
            }
        }


        /* =================================================
           RISK CARD COLOR
        ================================================= */

        const riskCard =
            document.querySelector(
                ".heat-risk"
            );

        if (riskCard) {

            riskCard.classList.remove(
                "risk-low",
                "risk-moderate",
                "risk-high",
                "risk-extreme"
            );


            const level =
                String(
                    riskLevel || ""
                ).toLowerCase();


            if (
                level.includes("extreme")
            ) {

                riskCard.classList.add(
                    "risk-extreme"
                );

            } else if (
                level.includes("high")
            ) {

                riskCard.classList.add(
                    "risk-high"
                );

            } else if (
                level.includes("moderate")
            ) {

                riskCard.classList.add(
                    "risk-moderate"
                );

            } else {

                riskCard.classList.add(
                    "risk-low"
                );
            }
        }


        /* =================================================
           SAFETY RECOMMENDATIONS
        ================================================= */

        const list =
            document.getElementById(
                "recommendations"
            );

        if (list) {

            list.innerHTML = "";


            const recommendations =
                stress.recommendations ??
                data.recommendations ??
                [];


            if (
                Array.isArray(recommendations) &&
                recommendations.length > 0
            ) {

                recommendations.forEach(
                    recommendation => {

                        const item =
                            document.createElement(
                                "li"
                            );

                        item.textContent =
                            recommendation;

                        list.appendChild(item);
                    }
                );

            } else {

                list.innerHTML =
                    "<li>No recommendations available.</li>";
            }
        }


        /* =================================================
           ML PREDICTION
        ================================================= */

        await loadMLPrediction(data);

    } catch (error) {

        console.error(
            "Weather error:",
            error
        );


        document.getElementById(
            "temperature"
        ).textContent = "--";

        document.getElementById(
            "humidity"
        ).textContent = "--";

        document.getElementById(
            "heatIndex"
        ).textContent = "--";

        document.getElementById(
            "wetBulb"
        ).textContent = "--";

        document.getElementById(
            "wbgt"
        ).textContent = "--";

        document.getElementById(
            "riskScore"
        ).textContent = "--";

        document.getElementById(
            "riskLevel"
        ).textContent = "--";

        document.getElementById(
            "riskCategory"
        ).textContent = "--";


        const list =
            document.getElementById(
                "recommendations"
            );

        if (list) {

            list.innerHTML =
                "<li>Unable to load weather recommendations.</li>";
        }
    }
}


/* =====================================================
   ML PREDICTION
===================================================== */

async function loadMLPrediction(
    weatherData
) {

    try {

        const stress =
            weatherData.thermal_stress || {};


        /* =================================================
           ML REQUEST
        ================================================= */

        const mlRequest = {

            zone_id: "TEST01",

            /*
             * IMPORTANT:
             * Use the currently selected location
             * instead of "Demo Metropolitan Area".
             */

            zone_name:
                CURRENT_LOCATION,

            temperature_c:
                weatherData.temperature_c ?? 0,

            humidity_percent:
                weatherData.relative_humidity ?? 0,

            wind_speed_kmh:
                weatherData.wind_speed_kmh ?? 0,

            solar_radiation_wm2:
                stress.solar_radiation_wm2 ?? 0,

            elderly_density:
                0.15,

            outdoor_worker_density:
                0.20,

            population_density:
                5000,

            healthcare_access:
                0.70,

            additional_features: {}
        };


        console.log(
            "ML Request:",
            mlRequest
        );


        const response =
            await fetch(
                `${API_BASE}/api/risk/predict`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            mlRequest
                        )
                }
            );


        if (!response.ok) {

            throw new Error(
                "ML prediction request failed"
            );
        }


        const mlData =
            await response.json();


        console.log(
            "ML Prediction:",
            mlData
        );


        const mlResult =
            mlData.ml_inference_result;


        if (
            mlResult &&
            mlResult.success
        ) {

            const mlScore =
                Number(
                    mlResult.risk_score
                );

            const mlLevel =
                String(
                    mlResult.risk_level || ""
                );


            /* =================================================
               MORTALITY RISK INDICATOR
            ================================================= */

            const mortalityScore =
                Math.max(
                    0,
                    Math.min(
                        100,
                        mlScore
                    )
                );


            let mortalityLevel;


            if (
                mortalityScore >= 75
            ) {

                mortalityLevel =
                    "Extreme";

            } else if (
                mortalityScore >= 50
            ) {

                mortalityLevel =
                    "High";

            } else if (
                mortalityScore >= 25
            ) {

                mortalityLevel =
                    "Moderate";

            } else {

                mortalityLevel =
                    "Low";
            }


            /* =================================================
               MORTALITY SCORE
            ================================================= */

            const mortalityScoreElement =
                document.getElementById(
                    "mortalityRiskScore"
                );


            if (
                mortalityScoreElement
            ) {

                mortalityScoreElement.textContent =
                    mortalityScore.toFixed(2);
            }


            /* =================================================
               MORTALITY LEVEL
            ================================================= */

            const mortalityLevelElement =
                document.getElementById(
                    "mortalityRiskLevel"
                );


            if (
                mortalityLevelElement
            ) {

                mortalityLevelElement.textContent =
                    mortalityLevel;
            }


            /* =================================================
               MORTALITY METER
            ================================================= */

            const mortalityMeter =
                document.getElementById(
                    "mortalityRiskMeterFill"
                );


            if (
                mortalityMeter
            ) {

                mortalityMeter.style.width =
                    `${mortalityScore}%`;


                if (
                    mortalityLevel === "Extreme"
                ) {

                    mortalityMeter.style.background =
                        "#dc2626";

                } else if (
                    mortalityLevel === "High"
                ) {

                    mortalityMeter.style.background =
                        "#ea580c";

                } else if (
                    mortalityLevel === "Moderate"
                ) {

                    mortalityMeter.style.background =
                        "#f59e0b";

                } else {

                    mortalityMeter.style.background =
                        "#16a34a";
                }
            }


            /* =================================================
               ML SCORE
            ================================================= */

            const scoreElement =
                document.getElementById(
                    "mlRiskScore"
                );


            if (
                scoreElement
            ) {

                scoreElement.textContent =
                    mlScore.toFixed(2);
            }


            /* =================================================
               ML LEVEL
            ================================================= */

            const levelElement =
                document.getElementById(
                    "mlRiskLevel"
                );


            if (
                levelElement
            ) {

                levelElement.textContent =
                    mlLevel;
            }


            /* =================================================
               ML METER
            ================================================= */

            const meter =
                document.getElementById(
                    "mlRiskMeterFill"
                );


            if (
                meter
            ) {

                const score =
                    Math.max(
                        0,
                        Math.min(
                            100,
                            mlScore
                        )
                    );


                meter.style.width =
                    `${score}%`;


                const level =
                    mlLevel.toLowerCase();


                if (
                    level.includes("extreme")
                ) {

                    meter.style.background =
                        "#dc2626";

                } else if (
                    level.includes("high")
                ) {

                    meter.style.background =
                        "#ea580c";

                } else if (
                    level.includes("moderate")
                ) {

                    meter.style.background =
                        "#f59e0b";

                } else {

                    meter.style.background =
                        "#16a34a";
                }
            }


        } else {

            console.error(
                "ML prediction unsuccessful:",
                mlResult
            );
        }


    } catch (error) {

        console.error(
            "ML Prediction Error:",
            error
        );


        const scoreElement =
            document.getElementById(
                "mlRiskScore"
            );


        if (
            scoreElement
        ) {

            scoreElement.textContent =
                "--";
        }


        const levelElement =
            document.getElementById(
                "mlRiskLevel"
            );


        if (
            levelElement
        ) {

            levelElement.textContent =
                "Unavailable";
        }
    }
}


/* =====================================================
   24-HOUR TEMPERATURE FORECAST
===================================================== */

async function loadTemperatureForecast() {

    const status =
        document.getElementById(
            "forecastStatus"
        );


    try {

        if (status) {

            status.textContent =
                "Loading forecast...";
        }


        const response =
            await fetch(
                `${API_BASE}/api/weather/forecast?lat=${LATITUDE}&lon=${LONGITUDE}&days=2`
            );


        if (!response.ok) {

            throw new Error(
                "Forecast API unavailable"
            );
        }


        const data =
            await response.json();


        console.log(
            "Forecast API response:",
            data
        );


        const hourly =
            data.hourly || {};


        const times =
            hourly.time || [];


        const temperatures =
            hourly.temperature_2m || [];


        if (
            times.length === 0 ||
            temperatures.length === 0
        ) {

            throw new Error(
                "No hourly forecast data available"
            );
        }


        /* Take the next 24 hours */

        const forecastTimes =
            times.slice(0, 24);


        const forecastTemperatures =
            temperatures.slice(0, 24);


        drawTemperatureChart(
            forecastTimes,
            forecastTemperatures
        );


        if (status) {

            status.textContent =
                "Showing temperature forecast for the next 24 hours.";
        }


    } catch (error) {

        console.error(
            "Forecast error:",
            error
        );


        if (status) {

            status.textContent =
                "Unable to load temperature forecast.";
        }
    }
}


/* =====================================================
   DRAW TEMPERATURE CHART
===================================================== */

function drawTemperatureChart(
    times,
    temperatures
) {

    const canvas =
        document.getElementById(
            "temperatureChart"
        );


    if (!canvas) {
        return;
    }


    const container =
        canvas.parentElement;


    const width =
        container.clientWidth || 700;


    const height =
        320;


    const dpr =
        window.devicePixelRatio || 1;


    canvas.width =
        width * dpr;


    canvas.height =
        height * dpr;


    canvas.style.width =
        `${width}px`;


    canvas.style.height =
        `${height}px`;


    const ctx =
        canvas.getContext("2d");


    ctx.scale(
        dpr,
        dpr
    );


    /* =================================================
       CHART PADDING
    ================================================= */

    const paddingLeft = 55;
    const paddingRight = 20;
    const paddingTop = 25;
    const paddingBottom = 45;


    const chartWidth =
        width -
        paddingLeft -
        paddingRight;


    const chartHeight =
        height -
        paddingTop -
        paddingBottom;


    /* =================================================
       MIN / MAX TEMPERATURE
    ================================================= */

    const numericTemps =
        temperatures.map(
            Number
        );


    let minTemp =
        Math.floor(
            Math.min(
                ...numericTemps
            ) - 2
        );


    let maxTemp =
        Math.ceil(
            Math.max(
                ...numericTemps
            ) + 2
        );


    if (
        minTemp === maxTemp
    ) {

        maxTemp =
            minTemp + 5;
    }


    /* =================================================
       BACKGROUND
    ================================================= */

    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    /* =================================================
       GRID LINES
    ================================================= */

    ctx.font =
        "12px Arial";


    ctx.textAlign =
        "right";


    ctx.textBaseline =
        "middle";


    const gridLines =
        5;


    for (
        let i = 0;
        i <= gridLines;
        i++
    ) {

        const value =
            minTemp +
            (
                (maxTemp - minTemp) *
                i /
                gridLines
            );


        const y =
            paddingTop +
            chartHeight -
            (
                chartHeight *
                i /
                gridLines
            );


        ctx.strokeStyle =
            "#e2e8f0";


        ctx.lineWidth =
            1;


        ctx.beginPath();


        ctx.moveTo(
            paddingLeft,
            y
        );


        ctx.lineTo(
            width -
            paddingRight,
            y
        );


        ctx.stroke();


        ctx.fillStyle =
            "#64748b";


        ctx.fillText(
            `${value.toFixed(0)}°`,
            paddingLeft - 10,
            y
        );
    }


    /* =================================================
       TEMPERATURE LINE
    ================================================= */

    const points = [];


    numericTemps.forEach(
        (
            temperature,
            index
        ) => {

            const x =
                paddingLeft +
                (
                    chartWidth *
                    index /
                    Math.max(
                        numericTemps.length - 1,
                        1
                    )
                );


            const y =
                paddingTop +
                chartHeight -
                (
                    (
                        temperature -
                        minTemp
                    )
                    /
                    (
                        maxTemp -
                        minTemp
                    )
                )
                *
                chartHeight;


            points.push({
                x,
                y,
                temperature
            });
        }
    );


    /* =================================================
       LINE
    ================================================= */

    ctx.beginPath();


    points.forEach(
        (
            point,
            index
        ) => {

            if (
                index === 0
            ) {

                ctx.moveTo(
                    point.x,
                    point.y
                );

            } else {

                ctx.lineTo(
                    point.x,
                    point.y
                );
            }
        }
    );


    ctx.strokeStyle =
        "#2563eb";


    ctx.lineWidth =
        3;


    ctx.lineJoin =
        "round";


    ctx.lineCap =
        "round";


    ctx.stroke();


    /* =================================================
       POINTS
    ================================================= */

    points.forEach(
        point => {

            ctx.beginPath();


            ctx.arc(
                point.x,
                point.y,
                4,
                0,
                Math.PI * 2
            );


            ctx.fillStyle =
                "#2563eb";


            ctx.fill();
        }
    );


    /* =================================================
       X-AXIS TIME LABELS
    ================================================= */

    ctx.fillStyle =
        "#64748b";


    ctx.font =
        "11px Arial";


    ctx.textAlign =
        "center";


    ctx.textBaseline =
        "top";


    points.forEach(
        (
            point,
            index
        ) => {

            /*
             * Show approximately every
             * 4 hours.
             */

            if (
                index % 4 !== 0 &&
                index !== points.length - 1
            ) {

                return;
            }


            const date =
                new Date(
                    times[index]
                );


            const label =
                date.toLocaleTimeString(
                    "en-IN",
                    {
                        hour: "2-digit",
                        minute: "2-digit",
                        hour12: true
                    }
                );


            ctx.fillText(
                label,
                point.x,
                height -
                paddingBottom +
                12
            );
        }
    );
}


/* =====================================================
   ACTIVE ALERTS
===================================================== */

async function loadAlerts() {

    try {

        const response =
            await fetch(
                `${API_BASE}/api/alerts/active`
            );


        if (!response.ok) {

            throw new Error(
                "Alerts unavailable"
            );
        }


        const data =
            await response.json();


        const alertsContainer =
            document.getElementById(
                "alerts"
            );


        alertsContainer.innerHTML =
            "";


        if (
            !data.active_alerts ||
            data.active_alerts.length === 0
        ) {

            alertsContainer.innerHTML = `
                <p>
                    No active heatwave alerts.
                </p>
            `;

            return;
        }


        data.active_alerts.forEach(
            alert => {

                const alertBox =
                    document.createElement(
                        "div"
                    );


                alertBox.className =
                    "alert-box";


                alertBox.innerHTML = `

                    <p class="alert-message">
                        🚨
                        <strong>
                            ${
                                alert.message ||
                                "Heatwave Warning"
                            }
                        </strong>
                    </p>

                    <p>
                        <strong>Zone:</strong>
                        ${
                            CURRENT_LOCATION ||
                            alert.zone_name ||
                            "--"
                        }
                    </p>

                    <p>
                        <strong>Alert Level:</strong>
                        ${
                            alert.alert_level ||
                            "--"
                        }
                    </p>

                    <p>
                        <strong>Severity:</strong>
                        ${
                            alert.severity ||
                            "--"
                        }
                    </p>

                    <p>
                        <strong>Valid From:</strong>
                        ${
                            formatDate(
                                alert.effective_from
                            )
                        }
                    </p>

                    <p>
                        <strong>Expires At:</strong>
                        ${
                            formatDate(
                                alert.expires_at
                            )
                        }
                    </p>
                `;


                alertsContainer.appendChild(
                    alertBox
                );
            }
        );


    } catch (error) {

        console.error(
            "Alerts error:",
            error
        );


        document.getElementById(
            "alerts"
        ).innerHTML =
            "<p>No alert data available.</p>";
    }
}


/* =====================================================
   DATE FORMAT
===================================================== */

function formatDate(
    dateString
) {

    if (!dateString) {
        return "--";
    }


    const date =
        new Date(
            dateString
        );


    if (
        isNaN(
            date.getTime()
        )
    ) {

        return dateString;
    }


    return date.toLocaleString(
        "en-IN",
        {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: true
        }
    );
}


/* =====================================================
   INITIALIZE DASHBOARD
===================================================== */

async function initializeDashboard() {

    await checkBackend();

    await checkModel();

    await loadWeather();

    await loadAlerts();

    await loadTemperatureForecast();
}


/* =====================================================
   START APPLICATION
===================================================== */

initializeDashboard();
