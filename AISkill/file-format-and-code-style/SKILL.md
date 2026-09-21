---
name: file-format-and-code-style
description: Preserve file encoding and whitespace when editing or creating files, and apply explicit code-style preferences for braces and spacing without unrelated formatting diffs.
---

# File Format and Code Style

- Before editing, inspect the original bytes and nearby code: encoding, BOM, CRLF/LF, final newline, tabs/spaces, indent width, and alignment.
- Preserve existing encoding, BOM, line endings, and final-newline state. Do not normalize mixed endings or add/remove a final newline unless requested.
- For new files, use the Windows defaults below unless the repository explicitly requires another format. Keep third-party code in its own format. Set encoding and line endings explicitly; do not rely on tool defaults.
- C# (`.cs`): UTF-8 with BOM, CRLF.
- C++ sources and headers (`.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hxx`, `.inl`): UTF-8 with BOM, CRLF.
- UE and Unity shaders (`.usf`, `.ush`, `.shader`, `.hlsl`, `.compute`, `.cginc`): UTF-8 without BOM, CRLF.
- These defaults do not authorize converting existing files. Preserve their format unless the user explicitly requests normalization; then apply the defaults within the requested scope.
- Preserve tabs versus spaces and indent width; never convert between them as an unrelated edit. Match nearby indentation, continuation alignment, and spacing without introducing inconsistent mixtures.
- Keep changes local; avoid whole-file formatting, whitespace cleanup, or encoding conversion.
- Apply these control-flow rules to new or modified bodies in brace-based languages:
- **Allman brace style:** Put opening and closing braces on separate lines, aligned with the control statement.
- **Always use braces:** Use braces for every control-flow body, even a single statement.
- **Space after control-flow keywords:** Write `if (x)`, not `if(x)`; likewise for `else if`, `for`, `while`, and `switch`. Keep function calls as `doThing()` with no space before `(`.
- Do not rewrite unrelated existing code just to enforce this preference.
- After writing, inspect the diff and file bytes. Remove accidental BOM, CRLF/LF, EOF-newline, indentation, or trailing-whitespace changes introduced by the edit. If the tool changes formatting automatically, restore the original format before finishing.
