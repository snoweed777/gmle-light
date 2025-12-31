import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff } from "lucide-react";
import {
  paramsDescriptions,
  getApiDescription,
  loggingDescriptions,
  httpDescriptions,
} from "@/lib/config-descriptions";

interface GlobalConfigSectionProps {
  data: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
  renderType?: "params" | "api" | "logging" | "http" | "rate_limit";
}

export default function GlobalConfigSection({
  data,
  onChange,
  renderType = "params",
}: GlobalConfigSectionProps) {
  const handleChange = (key: string, value: string) => {
    if (renderType === "params") {
      onChange(key, isNaN(Number(value)) ? value : Number(value));
    } else if (renderType === "http") {
      onChange(key, typeof value === "string" && !isNaN(Number(value)) ? Number(value) : value);
    } else {
      onChange(key, value);
    }
  };

  if (renderType === "params") {
    return (
      <div className="space-y-4">
        {Object.entries(data).map(([key, value]) => {
          const desc = paramsDescriptions[key];
          return (
            <div key={key}>
              <label className="text-sm font-medium mb-1 block">{key}</label>
              {desc && (
                <p className="text-xs text-muted-foreground mb-2">{desc.description}</p>
              )}
              {typeof value === "number" ? (
                <Input
                  type="number"
                  value={value}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder={desc?.recommended ? String(desc.recommended) : undefined}
                />
              ) : Array.isArray(value) ? (
                <Input
                  value={value.join(",")}
                  onChange={(e) =>
                    onChange(key, e.target.value.split(",").map((v) => v.trim()))
                  }
                  placeholder={
                    desc?.recommended && Array.isArray(desc.recommended)
                      ? desc.recommended.join(",")
                      : undefined
                  }
                />
              ) : (
                <Input
                  value={String(value)}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder={desc?.recommended ? String(desc.recommended) : undefined}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  }

  const updateNestedValue = (
    obj: Record<string, unknown>,
    path: string[],
    value: unknown
  ): Record<string, unknown> => {
    if (path.length === 1) {
      return { ...obj, [path[0]]: value };
    }
    const [first, ...rest] = path;
    return {
      ...obj,
      [first]: updateNestedValue(obj[first] as Record<string, unknown>, rest, value),
    };
  };

  const renderNestedObject = (
    parentKey: string,
    obj: Record<string, unknown>,
    path: string[] = [],
    level: number = 0
  ): JSX.Element => {
    // Check if this is ankiweb section and add password field if missing
    // ankiweb section can be at api.anki.ankiweb (parentKey="api", path=["anki", "ankiweb"])
    // or anki.ankiweb (parentKey="anki", path=["ankiweb"])
    const isAnkiwebSection = 
      (parentKey === "api" && path.length === 2 && path[0] === "anki" && path[1] === "ankiweb") ||
      (parentKey === "anki" && path.length === 1 && path[0] === "ankiweb") ||
      (path.length > 0 && path[path.length - 1] === "ankiweb");
    const shouldAddPassword = isAnkiwebSection && !("password" in obj);
    
    // Create entries list with password field if needed
    // For ankiweb section, ensure order: username, password, auto_login
    const entries = Object.entries(obj);
    if (shouldAddPassword) {
      // Insert password after username if it exists, otherwise at the beginning
      const usernameIndex = entries.findIndex(([key]) => key === "username");
      if (usernameIndex >= 0) {
        entries.splice(usernameIndex + 1, 0, ["password", ""]);
      } else {
        entries.unshift(["password", ""]);
      }
    } else if (isAnkiwebSection) {
      // Reorder entries: username, password, auto_login, others
      const orderedKeys = ["username", "password", "auto_login"];
      const orderedEntries: [string, unknown][] = [];
      const remainingEntries: [string, unknown][] = [];
      
      // Add ordered keys first
      for (const key of orderedKeys) {
        const entry = entries.find(([k]) => k === key);
        if (entry) {
          orderedEntries.push(entry);
        }
      }
      
      // Add remaining entries (excluding password_configured)
      for (const entry of entries) {
        if (!orderedKeys.includes(entry[0]) && entry[0] !== "password_configured") {
          remainingEntries.push(entry);
        }
      }
      
      // Combine ordered and remaining entries
      entries.length = 0;
      entries.push(...orderedEntries, ...remainingEntries);
    }
    
    return (
      <div className={level > 0 ? "pl-4 space-y-2 border-l-2" : "space-y-2"}>
        {entries.map(([subKey, subValue]) => {
          // Skip password_configured as it's read-only
          if (subKey === "password_configured") {
            return null;
          }
          
          // Avoid infinite loop: only add subKey if not already in path
          const currentPath = path.length === 0 || path[path.length - 1] !== subKey 
            ? [...path, subKey] 
            : path;
          const desc = path.length > 0 
            ? getApiDescription(parentKey, ...currentPath) 
            : getApiDescription(parentKey, subKey);
          
          if (typeof subValue === "boolean") {
            return (
              <div key={subKey}>
                <label className="text-xs text-muted-foreground mb-1 block">{subKey}</label>
                {desc && (
                  <p className="text-xs text-muted-foreground mb-2">{desc.description}</p>
                )}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={subValue}
                    onChange={(e) => {
                      const rootObj = data[parentKey] as Record<string, unknown>;
                      const newValue = updateNestedValue(rootObj, currentPath, e.target.checked);
                      onChange(parentKey, newValue);
                    }}
                  />
                  <span className="text-sm">{subValue ? "True" : "False"}</span>
                </div>
              </div>
            );
          } else if (typeof subValue === "object" && subValue !== null && !Array.isArray(subValue)) {
            return (
              <div key={subKey}>
                <label className="text-xs text-muted-foreground mb-1 block capitalize">{subKey}</label>
                {renderNestedObject(
                  parentKey,
                  subValue as Record<string, unknown>,
                  currentPath,
                  level + 1
                )}
              </div>
            );
          } else {
            // Check if this is a password field
            const isPasswordField = subKey === "password";
            
            // Check if password is configured (from API response)
            // Get ankiweb object from data structure: api.anki.ankiweb
            let ankiwebObj: any = null;
            if (parentKey === "api") {
              ankiwebObj = (data[parentKey] as any)?.anki?.ankiweb;
            } else if (parentKey === "anki") {
              ankiwebObj = (data[parentKey] as any)?.ankiweb;
            }
            const passwordConfigured = isPasswordField && 
              (ankiwebObj?.password_configured === true ||
               subValue === "••••••••••••••••");
            
            if (isPasswordField) {
              return (
                <PasswordField
                  key={subKey}
                  label={subKey}
                  description={desc?.description}
                  value={String(subValue || "")}
                  onChange={(value) => {
                    const rootObj = data[parentKey] as Record<string, unknown>;
                    const newValue = updateNestedValue(rootObj, currentPath, value);
                    onChange(parentKey, newValue);
                  }}
                  placeholder={desc?.recommended ? String(desc.recommended) : "Enter AnkiWeb password"}
                  isPassword={true}
                  isConfigured={passwordConfigured}
                />
              );
            }
            
            return (
              <div key={subKey}>
                <label className="text-xs text-muted-foreground mb-1 block">{subKey}</label>
                {desc && (
                  <p className="text-xs text-muted-foreground mb-2">{desc.description}</p>
                )}
                <Input
                  value={String(subValue || "")}
                  onChange={(e) => {
                    const rootObj = data[parentKey] as Record<string, unknown>;
                    const newValue = updateNestedValue(rootObj, currentPath, e.target.value);
                    onChange(parentKey, newValue);
                  }}
                  placeholder={desc?.recommended ? String(desc.recommended) : undefined}
                />
              </div>
            );
          }
        })}
      </div>
    );
  };

  if (renderType === "api") {
    return (
      <div className="space-y-4">
        {Object.entries(data).map(([key, value]) => {
          if (typeof value === "object" && value !== null) {
            return (
              <div key={key}>
                <label className="text-sm font-medium mb-1 block capitalize">{key}</label>
                {renderNestedObject(key, value as Record<string, unknown>)}
              </div>
            );
          }
          return (
            <div key={key}>
              <label className="text-sm font-medium mb-1 block">{key}</label>
              <Input value={String(value)} onChange={(e) => handleChange(key, e.target.value)} />
            </div>
          );
        })}
      </div>
    );
  }

  if (renderType === "logging") {
    return (
      <div className="space-y-4">
        {Object.entries(data).map(([key, value]) => {
          const desc = loggingDescriptions[key];
          return (
            <div key={key}>
              <label className="text-sm font-medium mb-1 block capitalize">{key}</label>
              {desc && (
                <p className="text-xs text-muted-foreground mb-2">{desc.description}</p>
              )}
              {key === "level" || key === "format" ? (
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={String(value)}
                  onChange={(e) => handleChange(key, e.target.value)}
                >
                  {key === "level" ? (
                    <>
                      <option value="DEBUG">DEBUG</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                    </>
                  ) : (
                    <>
                      <option value="human">human</option>
                      <option value="json">json</option>
                    </>
                  )}
                </select>
              ) : (
                <Input
                  type={key === "rotation_days" ? "number" : "text"}
                  value={value === null ? "" : String(value)}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder={desc?.recommended !== undefined ? String(desc.recommended) : undefined}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  }

  if (renderType === "http") {
    return (
      <div className="space-y-4">
        {Object.entries(data).map(([key, value]) => {
          const desc = httpDescriptions[key];
          return (
            <div key={key}>
              <label className="text-sm font-medium mb-1 block capitalize">{key}</label>
              {desc && (
                <p className="text-xs text-muted-foreground mb-2">{desc.description}</p>
              )}
              <Input
                type="number"
                value={Number(value)}
                onChange={(e) => handleChange(key, e.target.value)}
                placeholder={desc?.recommended ? String(desc.recommended) : undefined}
              />
            </div>
          );
        })}
      </div>
    );
  }

  if (renderType === "rate_limit") {
    return (
      <div className="space-y-4">
        {Object.entries(data).map(([key, value]) => {
          if (key === "enabled") {
            return (
              <div key={key}>
                <label className="text-sm font-medium mb-1 block">enabled</label>
                <p className="text-xs text-muted-foreground mb-2">レート制限を有効化</p>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={Boolean(value)}
                    onChange={(e) => onChange(key, e.target.checked)}
                  />
                  <span className="text-sm">{value ? "有効" : "無効"}</span>
                </div>
              </div>
            );
          }
          return (
            <div key={key}>
              <label className="text-sm font-medium mb-1 block">{key}</label>
              <p className="text-xs text-muted-foreground mb-2">
                {key === "requests_per_minute" && "1分あたりの最大リクエスト数"}
                {key === "requests_per_hour" && "1時間あたりの最大リクエスト数"}
                {key === "cooldown_seconds" && "レート制限到達時の待機時間（秒）"}
              </p>
              <Input
                type="number"
                value={Number(value)}
                onChange={(e) => onChange(key, Number(e.target.value))}
              />
            </div>
          );
        })}
      </div>
    );
  }

  return null;
}

interface PasswordFieldProps {
  label: string;
  description?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  isPassword: boolean;
  isConfigured?: boolean;
}

function PasswordField({
  label,
  description,
  value,
  onChange,
  placeholder,
  isPassword,
  isConfigured,
}: PasswordFieldProps) {
  const [showPassword, setShowPassword] = useState(false);
  // Only show masked password if it's configured AND no new value has been entered
  const displayValue = isPassword && isConfigured && !showPassword && value === "" ? "••••••••••••••••" : value;

  return (
    <div>
      <label className="text-xs text-muted-foreground mb-1 block">{label}</label>
      {description && (
        <p className="text-xs text-muted-foreground mb-2">{description}</p>
      )}
      <div className="flex gap-2">
        <Input
          type={isPassword && !showPassword ? "password" : "text"}
          value={displayValue}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="flex-1"
        />
        {isPassword && (
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

