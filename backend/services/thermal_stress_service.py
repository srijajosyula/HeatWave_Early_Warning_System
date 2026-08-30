import math
from typing import Dict, Any


class ThermalStressService:
    """
    Calculates thermal stress metrics including:
    - Heat Index
    - Wet-Bulb Temperature
    - Humidex
    - WBGT
    - Thermal risk score
    - Risk level
    - Safety recommendations
    """

    @staticmethod
    def calculate_heat_index(
        temperature_c: float,
        relative_humidity: float
    ) -> float:

        t_f = (temperature_c * 9.0 / 5.0) + 32.0
        rh = relative_humidity

        hi_simple = 0.5 * (
            t_f + 61.0
            + ((t_f - 68.0) * 1.2)
            + (rh * 0.094)
        )

        if hi_simple < 80.0:
            hi_f = hi_simple
        else:
            hi_f = (
                -42.379
                + 2.04901523 * t_f
                + 10.14333127 * rh
                - 0.22475541 * t_f * rh
                - 0.00683783 * (t_f ** 2)
                - 0.05481717 * (rh ** 2)
                + 0.00122874 * (t_f ** 2) * rh
                + 0.00085282 * t_f * (rh ** 2)
                - 0.00000199 * (t_f ** 2) * (rh ** 2)
            )

            if rh < 13.0 and 80.0 <= t_f <= 112.0:
                adjustment = (
                    ((13.0 - rh) / 4.0)
                    * math.sqrt(
                        (17.0 - abs(t_f - 95.0)) / 17.0
                    )
                )
                hi_f -= adjustment

            elif rh > 85.0 and 80.0 <= t_f <= 87.0:
                adjustment = (
                    ((rh - 85.0) / 10.0)
                    * ((87.0 - t_f) / 5.0)
                )
                hi_f += adjustment

        hi_c = (hi_f - 32.0) * 5.0 / 9.0

        return round(hi_c, 2)

    @staticmethod
    def calculate_wet_bulb_temperature(
        temperature_c: float,
        relative_humidity: float
    ) -> float:

        t = temperature_c
        rh = relative_humidity

        tw = (
            t * math.atan(
                0.151977 * math.sqrt(rh + 8.313659)
            )
            + math.atan(t + rh)
            - math.atan(rh - 1.676331)
            + 0.00391838
            * (rh ** 1.5)
            * math.atan(0.023101 * rh)
            - 4.686035
        )

        return round(tw, 2)

    @staticmethod
    def calculate_humidex(
        temperature_c: float,
        relative_humidity: float
    ) -> float:

        dew_point = temperature_c - (
            (100.0 - relative_humidity) / 5.0
        )

        e = 6.11 * math.exp(
            5417.7530
            * (
                1.0 / 273.16
                - 1.0 / (273.15 + dew_point)
            )
        )

        humidex = temperature_c + (
            5.0 / 9.0
        ) * (e - 10.0)

        return round(humidex, 2)

    @staticmethod
    def calculate_wbgt(
        temperature_c: float,
        relative_humidity: float,
        wind_speed_kmh: float,
        solar_radiation_wm2: float
    ) -> float:
        """
        Calculate WBGT using the formula from Laptop 1.

        Wind speed is converted from km/h to m/s.
        Solar radiation is converted from W/m² to kW/m².
        """

        wind_speed_ms = wind_speed_kmh / 3.6
        solar = solar_radiation_wm2 / 1000.0

        wbgt = (
            0.735 * temperature_c
            + 0.0374 * relative_humidity
            + 0.00292
            * temperature_c
            * relative_humidity
            + 7.619 * solar
            - 4.557 * (solar ** 2)
            - 0.0572 * wind_speed_ms
            - 4.064
        )

        return round(wbgt, 2)

    @staticmethod
    def calculate_wbgt_risk(wbgt: float) -> Dict[str, Any]:
        """
        Convert WBGT into a thermal stress score and level.
        """

        if wbgt < 25:
            score = 20
            level = "LOW"

        elif wbgt < 28:
            score = 40
            level = "MODERATE"

        elif wbgt < 32:
            score = 70
            level = "HIGH"

        else:
            score = 90
            level = "EXTREME"

        return {
            "score": score,
            "level": level
        }

    @staticmethod
    def get_recommendations(risk_level: str) -> list[str]:
        """
        Return safety recommendations based on thermal risk.
        """

        if risk_level == "LOW":
            return [
                "Normal outdoor activity is generally suitable.",
                "Stay hydrated throughout the day.",
                "Continue monitoring weather conditions."
            ]

        elif risk_level == "MODERATE":
            return [
                "Stay hydrated and drink water regularly.",
                "Take breaks in shaded or cool areas.",
                "Avoid prolonged outdoor activity during peak heat.",
                "Monitor yourself for signs of heat stress."
            ]

        elif risk_level == "HIGH":
            return [
                "Avoid prolonged outdoor activity.",
                "Drink water frequently.",
                "Take frequent breaks in shaded or cool areas.",
                "Schedule strenuous activities during cooler hours.",
                "Monitor for signs of heat stress."
            ]

        else:
            return [
                "Avoid strenuous outdoor activity.",
                "Move to a cool or shaded location.",
                "Drink water frequently.",
                "Use cooling measures whenever possible.",
                "Seek medical assistance if severe heat-stress symptoms occur."
            ]

    @classmethod
    def get_thermal_stress_summary(
        cls,
        temperature_c: float,
        relative_humidity: float,
        wind_speed_kmh: float = 0.0,
        solar_radiation_wm2: float = 0.0
    ) -> Dict[str, Any]:

        heat_index = cls.calculate_heat_index(
            temperature_c,
            relative_humidity
        )

        wet_bulb = cls.calculate_wet_bulb_temperature(
            temperature_c,
            relative_humidity
        )

        humidex = cls.calculate_humidex(
            temperature_c,
            relative_humidity
        )

        wbgt = cls.calculate_wbgt(
            temperature_c,
            relative_humidity,
            wind_speed_kmh,
            solar_radiation_wm2
        )

        wbgt_risk = cls.calculate_wbgt_risk(wbgt)

        risk_level = wbgt_risk["level"]
        risk_score = wbgt_risk["score"]

        if heat_index < 27:
            thermal_category = "Normal / Safe"

        elif heat_index < 32:
            thermal_category = "Caution"

        elif heat_index < 41:
            thermal_category = "Extreme Caution"

        elif heat_index < 54:
            thermal_category = "Danger"

        else:
            thermal_category = "Extreme Danger"

        return {
            "temperature_c": temperature_c,
            "relative_humidity": relative_humidity,
            "wind_speed_kmh": wind_speed_kmh,
            "solar_radiation_wm2": solar_radiation_wm2,
            "heat_index_c": heat_index,
            "wet_bulb_temperature_c": wet_bulb,
            "humidex_c": humidex,
            "wbgt_c": wbgt,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "thermal_category": thermal_category,
            "recommendations": cls.get_recommendations(risk_level)
        }
if __name__ == "__main__":
    result = ThermalStressService.get_thermal_stress_summary(42.0, 55.0)
    print(result)