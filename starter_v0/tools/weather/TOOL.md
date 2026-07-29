# Tool: weather

## Mô tả

Tool lấy thời tiết hiện tại và dự báo cho bất kỳ thành phố nào trên thế giới, sử dụng Open-Meteo API (miễn phí, không cần API key).

## Khi nào dùng

- User hỏi thời tiết hôm nay ở một địa điểm cụ thể
- User muốn biết nhiệt độ, lượng mưa, độ ẩm, tốc độ gió
- User muốn dự báo 3–7 ngày tới

## Khi nào KHÔNG dùng

- Không có địa điểm cụ thể → gọi `clarify` trước để hỏi địa điểm
- Hỏi thời tiết lịch sử (quá khứ xa) → không hỗ trợ
- Câu hỏi không liên quan đến thời tiết thực tế

## Arguments

| Tên | Kiểu | Required | Mặc định | Mô tả |
|---|---|---|---|---|
| location | string | ✅ | — | Tên thành phố (VD: "Hanoi", "Hà Nội", "Ho Chi Minh City", "Paris") |
| days | integer | ❌ | 1 | Số ngày dự báo (1=hôm nay, tối đa 7) |

## Return format

```json
{
  "location": "Hanoi",
  "latitude": 21.0245,
  "longitude": 105.8412,
  "timezone": "Asia/Bangkok",
  "current": {
    "temperature_c": 31.2,
    "feels_like_c": 36.5,
    "humidity_pct": 78,
    "wind_speed_kmh": 12.5,
    "weather_description": "Partly Cloudy",
    "precipitation_mm": 0.0
  },
  "forecast": [
    {
      "date": "2026-07-29",
      "temp_max_c": 34.0,
      "temp_min_c": 27.0,
      "precipitation_sum_mm": 5.2,
      "weather_description": "Rain Showers"
    }
  ],
  "error": null,
  "message": "Weather data for Hanoi fetched successfully"
}
```

## Quicktest

```powershell
cd starter_v0
python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['weather'](location='Hanoi'); print({'error': r.get('error'), 'temp': r.get('current', {}).get('temperature_c')})"
```

## API sử dụng

- **Geocoding**: [Open-Meteo Geocoding API](https://geocoding-api.open-meteo.com/v1/search) — chuyển tên thành phố thành lat/lon
- **Weather**: [Open-Meteo Weather API](https://api.open-meteo.com/v1/forecast) — lấy dữ liệu thời tiết
- **Miễn phí**: Không cần API key, không cần đăng ký
- **Rate limit**: Generous free tier, đủ cho demo/lab

## WMO Weather Code Mapping

Tool tự động dịch WMO weather codes thành mô tả tiếng Anh (Clear, Cloudy, Rain, Snow, Thunderstorm, etc.).
