# Grayscale Screen Streaming Protocol / Протокол потоковой передачи в оттенках серого

## English
- Purpose: stream pygame screen contents as grayscale with a compact, restart-friendly framing.
- Start-of-frame command: single byte `0xA5`, immediately followed by ASCII magic `IVG`.
- Header (little-endian, total 17 bytes):  
  `start (0xA5) | magic (3s) | version (u8) | frame_id (u32) | width (u16) | height (u16) | payload_len (u32)`.  
  `version` starts at `1`. `payload_len` is the number of bytes that follow in the payload.
- Payload: sequence of run records, each 7 bytes, little-endian:  
  `offset (u32) | gray (u8) | run_len (u16)`.  
  `offset` is the absolute pixel index starting at 0, scanning left-to-right, top-to-bottom. `run_len` counts how many consecutive pixels carry `gray`, capped at `65535`.
- Grayscale: derived per pixel as `gray = int(0.299 * r + 0.587 * g + 0.114 * b)` using the RGB values read from the source surface.
- End-of-frame: reached after exactly `payload_len` bytes are read; expected pixels = `width * height`. Receivers should validate that the final filled pixel count matches.
- Resync strategy: on corruption, scan for `0xA5 49 56 47` (start byte + `IVG`), read the next 13 header bytes, then consume `payload_len`. Because every run ships its absolute `offset`, receivers can drop or skip corrupted runs and still place later runs correctly.
- Transport: designed for both TCP sockets and raw serial streams. TCP is recommended for reliability; serial links should run with a binary-safe mode and sufficient baud rate (e.g., `115200`).

## Русский
- Назначение: компактно передавать содержимое окна pygame в оттенках серого с возможностью восстановления при потере пакетов.
- Команда начала кадра: байт `0xA5`, за которым сразу идут ASCII-символы `IVG`.
- Заголовок (little-endian, 17 байт):  
  `start (0xA5) | magic (3s) | version (u8) | frame_id (u32) | width (u16) | height (u16) | payload_len (u32)`.  
  `version` начинается с `1`. `payload_len` — количество байт в полезной нагрузке.
- Полезная нагрузка: последовательность записей по 7 байт в формате little-endian:  
  `offset (u32) | gray (u8) | run_len (u16)`.  
  `offset` — абсолютный индекс пикселя, считая слева направо и сверху вниз. `run_len` — количество одинаковых пикселей (`gray`), максимум `65535`.
- Оттенок серого: `gray = int(0.299 * r + 0.587 * g + 0.114 * b)` для RGB-пикселей исходной поверхности.
- Конец кадра: наступает после чтения ровно `payload_len` байт; ожидаемое число пикселей — `width * height`. Приёмник должен сверить итоговый размер.
- Восстановление: при порче данных ищите последовательность `0xA5 49 56 47` (стартовый байт + `IVG`), считайте следующие 13 байт заголовка и затем `payload_len` байт. Так как каждая запись содержит абсолютный `offset`, приёмник может пропускать повреждённые участки и всё равно правильно разместить более поздние участки кадра.
- Транспорт: подходит для TCP-сокетов и «сырого» сериала. Рекомендуется TCP для надёжности; для последовательного порта используйте двоичный режим и подходящую скорость (например, `115200` бод).
