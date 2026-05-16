#!/usr/bin/env bash
set -u

out="context_dump.txt"

files=(
  "src/main.py"
)

dirs=(
  "src/app"
  "src/application"
  "src/domain"
  "src/infrastructure"
)

: > "$out"

dump_file() {
  local file="$1"

  printf '%s\n```\n' "$file" >> "$out"
  cat "$file" >> "$out"
  printf '\n```\n\n' >> "$out"
}

for file in "${files[@]}"; do
  if [[ -f "$file" ]]; then
    dump_file "$file"
  else
    echo "Skipping missing file: $file" >&2
  fi
done

for dir in "${dirs[@]}"; do
  if [[ -d "$dir" ]]; then
    while IFS= read -r file; do
      dump_file "$file"
    done < <(find "$dir" -type f -name '*.py' | sort)
  else
    echo "Skipping missing directory: $dir" >&2
  fi
done

echo "Created: $out"  