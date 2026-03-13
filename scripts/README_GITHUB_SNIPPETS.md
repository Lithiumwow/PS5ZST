# PS5 Compression Quick Scripts (ZST Only)

## 1) Build PS5 decompressor ELF (WSL)

From the workspace root:

wsl bash zstd_deploy/scripts/build_decompress_elf_wsl.sh zstd_deploy/decompress_ps5.c zstd_deploy/decompress_ps5_ps5.elf

## 2) Create compressed ZST package folder + manifest (WSL)

From the workspace root:

wsl bash zstd_deploy/scripts/pack_zst_manifest_wsl.sh PPSA17221-app PPSA17221-compressed 3

## Notes

- Script 1 downloads a prebuilt ps5-payload-sdk in /tmp if missing and builds the ELF.
- Script 2 creates .zst files plus manifest.txt using compress_pkg.py.
- On PS5, use manifest mode in decompress_ps5.elf.
