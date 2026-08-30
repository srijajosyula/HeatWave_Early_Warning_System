from typing import Dict, Any, List


class AlertService:
    """
    Early Warning and Recommendation Engine.
    Evaluates meteorological parameters and thermal stress to generate
    standardized heatwave alert levels and actionable public health advisories.
    """

    @staticmethod
    def evaluate_alert(
        temperature_c: float,
        heat_index_c: float,
        zone_name: str = "General Area"
    ) -> Dict[str, Any]:
        """
        Evaluate thermal indicators and return early warning tier and advisories.
        """
        if heat_index_c >= 45.0 or temperature_c >= 45.0:
            level = "RED"
            alert_name = "Red Alert - Severe Heatwave Emergency"
            severity = "CRITICAL"
            color = "#EF4444"
            summary = f"Severe heatwave conditions detected in {zone_name}. High risk of heat stroke and severe health impacts."
            actions = [
                "Avoid going outdoors between 11:00 AM and 4:00 PM.",
                "Municipalities should deploy water tankers and emergency cooling stations.",
                "Hospitals must prepare emergency heat stroke units and stock IV fluids.",
                "Suspend strenuous outdoor labor and construction work."
            ]
        elif heat_index_c >= 40.0 or temperature_c >= 42.0:
            level = "ORANGE"
            alert_name = "Orange Alert - Heatwave Warning"
            severity = "HIGH"
            color = "#F97316"
            summary = f"Heatwave conditions prevailing in {zone_name}. Significant heat stress for vulnerable populations."
            actions = [
                "Stay hydrated and avoid direct sunlight exposure.",
                "Provide frequent shaded rest breaks and hydration for outdoor workers.",
                "Monitor elderly, children, and people with chronic health conditions.",
                "Ensure pets and livestock have shaded shelters and adequate water."
            ]
        elif heat_index_c >= 33.0 or temperature_c >= 38.0:
            level = "YELLOW"
            alert_name = "Yellow Alert - Heatwave Watch"
            severity = "MODERATE"
            color = "#EAB308"
            summary = f"Elevated thermal stress in {zone_name}. Heat discomfort is likely."
            actions = [
                "Drink plenty of water even if not feeling thirsty.",
                "Wear loose, lightweight, light-colored cotton clothing.",
                "Use umbrellas, hats, or sunglasses when stepping outdoors.",
                "Keep living spaces ventilated or cool."
            ]
        else:
            level = "GREEN"
            alert_name = "Green - Normal Conditions"
            severity = "LOW"
            color = "#22C55E"
            summary = f"Normal thermal conditions in {zone_name}. No heatwave warning in effect."
            actions = [
                "Maintain standard daily hydration.",
                "No immediate heatwave restrictions."
            ]

        return {
            "zone": zone_name,
            "alert_level": level,
            "alert_name": alert_name,
            "severity": severity,
            "color_code": color,
            "summary": summary,
            "advisories": {
                "general_public": actions,
                "vulnerable_groups": [
                    "Keep elderly individuals in well-ventilated or air-cooled rooms.",
                    "Ensure infants and young children drink water regularly.",
                    "Check on neighbors living alone."
                ],
                "outdoor_workers": [
                    "Schedule heavy physical work during cooler morning hours (before 10:00 AM).",
                    "Take 15-minute breaks in the shade every hour during peak sun."
                ]
            }
        }
