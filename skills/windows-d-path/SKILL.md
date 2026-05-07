---
name: windows-d-path
description: Convert Windows drive-letter paths to WSL /mnt/<drive>/... paths whenever the user mentions, pastes, or asks about paths like C:\\..., D:\\..., or E:\\.... Use this skill proactively for raw Windows-style paths, quoted paths, escaped paths, mixed Windows/WSL path discussions, or requests like "fix this path" and "convert this file path", even if the user does not explicitly mention WSL.
---

# Windows Drive Path

Use this skill when the user provides a Windows path with a drive letter and needs the WSL equivalent.

## Goal

Turn Windows paths such as `C:\...`, `D:\...`, and `E:\...` into WSL paths under `/mnt/c/...`, `/mnt/d/...`, and `/mnt/e/...`.

## Conversion rules

1. Detect the drive prefix such as `C:\`, `D:\`, `E:\`, or the slash form `C:/`, `D:/`, `E:/`.
2. Convert the drive letter to lowercase in the mount point: `C:` → `/mnt/c/`, `D:` → `/mnt/d/`, `E:` → `/mnt/e/`.
3. Replace all remaining backslashes `\` with forward slashes `/`.
4. Preserve the rest of the path segments exactly.
5. Keep spaces, dots, Unicode characters, and file extensions unchanged.
6. If the path is wrapped in quotes, return the converted path in the same quoting style unless the user asks otherwise.

## Examples

- `C:\Users\light\notes.txt` → `/mnt/c/Users/light/notes.txt`
- `D:\text.txt` → `/mnt/d/text.txt`
- `E:\Media Files\demo.mp4` → `/mnt/e/Media Files/demo.mp4`
- `"D:\Projects\test data\input.csv"` → `"/mnt/d/Projects/test data/input.csv"`
- `C:/logs/app.log` → `/mnt/c/logs/app.log`

## Response style

- If the user gives a single path, respond with just the converted path unless they ask for explanation.
- If the user gives multiple paths, convert each one clearly and keep the same order.
- If the user asks how to do the conversion, briefly explain the rule: `<drive>:\` becomes `/mnt/<drive-lower>/`, and `\` becomes `/`.

## Edge handling

- Apply this skill to Windows drive-letter paths that map naturally to WSL mounts.
- At minimum, handle `C:`, `D:`, and `E:` correctly.
- Do not invent files or guess whether a path exists.
- If the input is ambiguous or malformed, state the most likely converted form and note the ambiguity briefly.
