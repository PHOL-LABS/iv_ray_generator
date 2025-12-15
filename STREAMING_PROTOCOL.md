# Screen Streaming Protocol (Grayscale & B/W) / Протокол потоковой передачи (оттенки серого и Ч/Б)

## English
- Purpose: stream pygame screen contents in grayscale or black/white with compact, restart-friendly framing.
- Start-of-frame marker: byte `0xA5` followed by ASCII magic `IVG`.
- Header (little-endian, 18 bytes):  
  `start (0xA5) | magic (3s) | version (u8) | flags (u8) | frame_id (u32) | width (u16) | height (u16) | payload_len (u32)`.  
  - `version`: starts at `1`.  
  - `flags`: bit0 = `1` means black/white mode; `0` means grayscale mode.  
  - `payload_len`: number of bytes that follow.
- Grayscale payload (flags bit0 = 0): sequence of run records, each 7 bytes, little-endian:  
  `offset (u32) | gray (u8) | run_len (u16)`.  
  `offset` is absolute pixel index (row-major). `run_len` is capped at `65535`.
- Black/white payload (flags bit0 = 1): runs of only “set” (white) pixels, each 6 bytes:  
  `offset (u32) | run_len (u16)`.  
  Background is implicit black; any pixels not covered by a run stay black. Threshold on sender: gray >= 128 → white, otherwise black.
- Grayscale conversion: `gray = int(0.299 * r + 0.587 * g + 0.114 * b)` from the source surface.
- End-of-frame: reached after reading `payload_len` bytes; expected pixels = `width * height`. Receivers should validate coverage.
- Resync: on corruption, scan for `0xA5 49 56 47` (start byte + `IVG`), read the next 14 header bytes, then consume `payload_len`. Because each run has an absolute `offset`, receivers can skip bad runs and still place later runs correctly.
- Transport: works over TCP or serial (pyserial). Prefer TCP for reliability; for serial use a binary-safe link and matching baud (e.g., `115200`, `921600`).

## Русский
- Назначение: передавать содержимое окна pygame в оттенках серого или в чёрно-белом виде с компактным кадрированием и возможностью восстановления.
- Маркер начала кадра: байт `0xA5`, затем ASCII-магия `IVG`.
- Заголовок (little-endian, 18 байт):  
  `start (0xA5) | magic (3s) | version (u8) | flags (u8) | frame_id (u32) | width (u16) | height (u16) | payload_len (u32)`.  
  - `version`: начинается с `1`.  
  - `flags`: бит0 = `1` — чёрно-белый режим; `0` — градации серого.  
  - `payload_len`: количество последующих байт.
- Полезная нагрузка в градациях серого (бит0 = 0): записи по 7 байт:  
  `offset (u32) | gray (u8) | run_len (u16)`.  
  `offset` — абсолютный индекс пикселя (построчно). `run_len` — длина последовательности, максимум `65535`.
- Полезная нагрузка Ч/Б (бит0 = 1): только участки “включённых” (белых) пикселей по 6 байт:  
  `offset (u32) | run_len (u16)`.  
  Фон подразумевается чёрным; всё не покрытое участками остаётся чёрным. Порог на отправителе: gray >= 128 → белый, иначе чёрный.
- Перевод в серый: `gray = int(0.299 * r + 0.587 * g + 0.114 * b)` из исходной поверхности.
- Конец кадра: после чтения `payload_len` байт; ожидаемое число пикселей = `width * height`. Приёмник должен сверять покрытие.
- Восстановление: при повреждении ищите `0xA5 49 56 47` (стартовый байт + `IVG`), читайте следующие 14 байт заголовка и затем `payload_len`. Так как каждое звено содержит абсолютный `offset`, приёмник может пропускать плохие записи и всё равно верно размещать последующие.
- Транспорт: TCP или serial (pyserial). TCP предпочтителен; для последовательного порта используйте двоичный режим и согласованный baud (например, `115200`, `921600`).
