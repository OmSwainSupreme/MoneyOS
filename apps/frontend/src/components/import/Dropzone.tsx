import { useCallback, useId, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

export interface DropzoneProps {
  onFile: (file: File) => void;
  maxBytes?: number;
  accept?: string[];
}

const DEFAULT_ACCEPT = [".csv", ".json"];
const DEFAULT_MAX = 5 * 1024 * 1024;

function extensionOf(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx).toLowerCase() : "";
}

export function Dropzone({
  onFile,
  maxBytes = DEFAULT_MAX,
  accept = DEFAULT_ACCEPT,
}: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOver, setOver] = useState(false);
  const helpId = useId();
  const errorId = useId();

  const handleFile = useCallback(
    (file: File) => {
      const ext = extensionOf(file.name);
      if (!accept.includes(ext)) {
        setError(`Unsupported file type ${ext || "(unknown)"}. Allowed: ${accept.join(", ")}`);
        return;
      }
      if (file.size > maxBytes) {
        setError(`File too large (${(file.size / 1024 / 1024).toFixed(2)} MB). Max ${(maxBytes / 1024 / 1024).toFixed(0)} MB.`);
        return;
      }
      setError(null);
      onFile(file);
    },
    [accept, maxBytes, onFile],
  );

  const open = () => inputRef.current?.click();

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a CSV or JSON statement"
        aria-describedby={`${helpId} ${error ? errorId : ""}`.trim()}
        onClick={open}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            open();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        className={`flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed p-6 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
          isOver
            ? "border-primary bg-accent"
            : "border-border bg-card hover:bg-accent"
        }`}
      >
        <UploadCloud aria-hidden className="h-6 w-6 text-muted-foreground" />
        <span className="font-medium text-foreground">
          Drop a file or click to browse
        </span>
        <span id={helpId} className="text-xs text-muted-foreground">
          {accept.join(", ")} · up to {(maxBytes / 1024 / 1024).toFixed(0)} MB · parsed in-browser
        </span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={accept.join(",")}
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      {error ? (
        <p id={errorId} role="alert" className="mt-2 text-sm text-[color:var(--color-danger-zone)]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
