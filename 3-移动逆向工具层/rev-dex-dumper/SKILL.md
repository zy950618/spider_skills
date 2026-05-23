---
name: rev-dex-dumper
description: Dump DEX files from a running Android app for unpacking/deobfuscation. Activate when the user wants to unpack an Android APK (including packers like 360 加固 / 腾讯乐固 / 梆梆 / 爱加密), dump DEX from memory, extract decrypted DEX files, or defeat class-loading packing.
platforms: [app]
---

# rev-dex-dumper - Android DEX Dumper

Dump DEX files from a running Android application's memory using `panda-dex-dumper` via ADB.

---

## Tool Location

The `panda-dex-dumper` binary is bundled in this skill's directory. Resolve its absolute path relative to this SKILL.md file:

```
skills/rev-dex-dumper/panda-dex-dumper
```

---

## Workflow

### 1. Push the tool to device

```bash
adb push <path-to>/panda-dex-dumper /data/local/tmp/
adb shell chmod +x /data/local/tmp/panda-dex-dumper
```

### 2. Determine target package name

If the user provides a package name, use it directly. Otherwise, get the foreground app:

```bash
adb shell dumpsys activity top | grep 'ACTIVITY' | tail -1 | awk '{print $2}' | cut -d/ -f1
```

### 3. Run the dumper

```bash
adb shell "cd /data/local/tmp && ./panda-dex-dumper -p $(adb shell pidof <package_name>)"
```

The dumped DEX files are saved to `/data/local/tmp/panda/` on the device.

### 4. Pull DEX files to host

```bash
adb pull /data/local/tmp/panda/ ./
```

Pull to the user's current working directory.

### 5. Clean up device cache

```bash
adb shell rm -rf /data/local/tmp/panda/
adb shell rm /data/local/tmp/panda-dex-dumper
```

---

## Guidelines

1. **Always verify ADB connection first** — run `adb devices` and confirm a device is listed before proceeding.
2. **Root may be required** — `panda-dex-dumper` uses `ptrace` to attach to the target process. If the device is not rooted, the dump will fail. Suggest `adb root` or running via `su` if needed.
3. **Wait for app to fully load** — if the user is dumping a packed app, the real DEX is only available after the packer's class loader has decrypted it. Advise the user to navigate past the splash screen before dumping.
4. **Handle pidof failure** — if `pidof` returns empty, the app may not be running. Launch it first with `adb shell monkey -p <package_name> -c android.intent.category.LAUNCHER 1`.
5. **Multiple DEX files are normal** — packed apps often produce several DEX files. All files in `/data/local/tmp/panda/` should be pulled.
6. **Always clean up** — remove both the dumped DEX files and the tool binary from the device after pulling results to avoid leaving artifacts.

---

## Tool Policy

- **开始实现前 Read `~/.claude/skills/karpathy-guidelines/SKILL.md`**,确认 4 条原则:Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution。这是基础层规范,所有执行类 skill 强制依赖。
- **遇到逆向运行时问题(断点/时间/cookie/TLS 指纹/风控恢复/接口变更)Read `~/.claude/skills/my_reverse_skill/99-SKILLS治理/10-逆向运行时常见问题.md`**。
