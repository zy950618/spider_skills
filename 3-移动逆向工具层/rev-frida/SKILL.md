---
name: rev-frida
description: Generate Frida hook scripts using modern Frida API. Activate when the user wants to write Frida scripts, hook functions at runtime, trace calls/arguments/return values, intercept native or ObjC/Java methods, or dump memory and exports.
platforms: [app]
---

# rev-frida - Frida Script Generator

Generate Frida instrumentation scripts for dynamic analysis, hooking, and runtime inspection.

---

## Important: Modern Frida CLI

The new Frida CLI **does not have** a `--no-pause` flag. The process resumes automatically.

```bash
# Spawn and hook (process starts after script loads)
frida -U -f com.example.app -l hook.js

# Attach to running process
frida -U com.example.app -l hook.js

# Attach by PID
frida -U -p 1234 -l hook.js
```

---

## Modern API Reference

### Module & Symbol Lookup

```javascript
// Get a loaded module by name
var mod = Process.getModuleByName("libssl.so");

// Module properties
mod.name    // "libssl.so"
mod.base    // NativePointer - base address
mod.size    // module size in bytes
mod.path    // full filesystem path

// Get export address directly
var ptr = mod.getExportByName("SSL_read");

// Enumerate all loaded modules
Process.enumerateModules()
// Returns: [{ name, base, size, path }, ...]

// Enumerate exports of a module
mod.enumerateExports()
// Returns: [{ type, name, address }, ...]

// Enumerate imports of a module
mod.enumerateImports()
// Returns: [{ type, name, module, address }, ...]

// Find export across all modules
var addr = Module.getExportByName(null, "open");
```

### Interceptor

```javascript
Interceptor.attach(ptr, {
    onEnter(args) {
        // args[0], args[1], ... are NativePointer
        console.log("arg0:", args[0].toInt32());
        console.log("arg1 str:", args[1].readUtf8String());
    },
    onLeave(retval) {
        console.log("ret:", retval.toInt32());
        // retval.replace(ptr(0x1));  // modify return value
    }
});

// Replace function implementation entirely
Interceptor.replace(ptr, new NativeCallback(function (a0, a1) {
    console.log("replaced!");
    return 0;
}, 'int', ['pointer', 'int']));
```

### NativeFunction & NativeCallback

```javascript
// Call a native function from JS
var open = new NativeFunction(
    Module.getExportByName(null, "open"),
    'int', ['pointer', 'int']
);
var fd = open(Memory.allocUtf8String("/etc/hosts"), 0);

// Create a callback for native code to call
var cb = new NativeCallback(function (arg) {
    console.log("called with:", arg);
    return 0;
}, 'int', ['int']);
```

### Memory Operations

```javascript
// Read
ptr(addr).readByteArray(size)    // ArrayBuffer
ptr(addr).readUtf8String()       // string
ptr(addr).readU32()              // number
ptr(addr).readPointer()          // NativePointer

// Write
ptr(addr).writeByteArray(bytes)
ptr(addr).writeUtf8String("hello")
ptr(addr).writeU32(0x41414141)

// Allocate
var buf = Memory.alloc(256);
var str = Memory.allocUtf8String("hello");

// Scan memory for pattern
Memory.scan(mod.base, mod.size, "48 89 5C 24 ?? 48 89 6C", {
    onMatch(address, size) {
        console.log("found at:", address);
    },
    onComplete() {}
});
```

### ObjC (iOS/macOS)

```javascript
if (ObjC.available) {
    var NSString = ObjC.classes.NSString;

    // Hook ObjC method
    var hook = ObjC.classes.ClassName["- methodName:"];
    Interceptor.attach(hook.implementation, {
        onEnter(args) {
            // args[0] = self, args[1] = _cmd, args[2] = first param
            var self = new ObjC.Object(args[0]);
            var param = new ObjC.Object(args[2]);
            console.log("self:", self.toString());
            console.log("param:", param.toString());
        }
    });

    // Enumerate classes
    Object.keys(ObjC.classes).filter(c => c.includes("KeyChain"));
}
```

### Java (Android)

```javascript
if (Java.available) {
    Java.perform(function () {
        var Activity = Java.use("android.app.Activity");
        Activity.onCreate.implementation = function (bundle) {
            console.log("onCreate called");
            this.onCreate(bundle);
        };

        // Enumerate loaded classes
        Java.enumerateLoadedClasses({
            onMatch(name) {
                if (name.includes("crypto")) console.log(name);
            },
            onComplete() {}
        });
    });
}
```

---

## Script Generation Guidelines

When generating Frida scripts:

1. **Always use modern API** — `Process.getModuleByName()`, `mod.getExportByName()`, not deprecated `Module.findBaseAddress()`
2. **No `--no-pause`** — the new Frida CLI does not support this flag
3. **Handle module load timing** — if hooking early, check if the module is loaded first:
   ```javascript
   function hookWhenReady(moduleName, exportName, callbacks) {
       var mod = Process.findModuleByName(moduleName);
       if (mod) {
           Interceptor.attach(mod.getExportByName(exportName), callbacks);
       } else {
           var interval = setInterval(function () {
               mod = Process.findModuleByName(moduleName);
               if (mod) {
                   clearInterval(interval);
                   Interceptor.attach(mod.getExportByName(exportName), callbacks);
               }
           }, 100);
       }
   }
   ```
4. **Print hex for pointers** — use `ptr.toString(16)` or `hexdump(ptr, { length: 64 })`
5. **Wrap in try/catch** for robustness in production hooks
6. **Use `hexdump()`** for binary data inspection:
   ```javascript
   console.log(hexdump(args[0], { offset: 0, length: 64, header: true, ansi: false }));
   ```

---

## Tool Policy

- **开始实现前 Read `~/.claude/skills/karpathy-guidelines/SKILL.md`**,确认 4 条原则:Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution。这是基础层规范,所有执行类 skill 强制依赖。
- **遇到逆向运行时问题(断点/时间/cookie/TLS 指纹/风控恢复/接口变更)Read `~/.claude/skills/my_reverse_skill/99-SKILLS治理/10-逆向运行时常见问题.md`**。
