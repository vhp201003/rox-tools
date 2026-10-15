# 06 — Automation Engineering Guide

> **Scope:** Research reference for protocol-level automation against Ragnarok X: Next Generation (`0616_h5.apk`). All data sourced from static analysis of `Assembly-CSharp.dll`, extracted config tables, and unstripped `libil2cpp.so`. No server-side exploitation is implied.

---

## 1. Architecture Decision: Two Viable Routes

| Dimension | Route A — Headless Socket Bot | Route B — Frida In-Process Hook |
|---|---|---|
| **How it works** | Standalone Node/Python process opens a raw TCP/WebSocket connection, speaks the game protocol, authenticates, and issues packets | Frida attaches to the live game process, hooks managed C# methods via `libil2cpp.so` exports, intercepts calls at runtime |
| **Detection surface** | New device fingerprint + unusual traffic patterns | Process injection triggers ByteDance GameProtect (`libhhld-rt.so`) integrity checks |
| **Complexity** | High — must replicate full auth handshake (GSDK JWT → session token → protocol login) | Medium — function addresses are free (unstripped `.dynsym`), no offset guessing |
| **Stability** | Breaks on server-side protocol changes | Breaks on game binary updates only |
| **Best for** | Market Sniper, Daily Board, item purchase loops | Auto Fishing, UI-triggered enchanting, spawn-point navigation |

---

## 2. Route A — Headless Socket Bot

### 2.1 Auth Flow

```
[Bot] → POST https://login-sg.bytegsdk.com/sdk/login
        Body: { app_id, device_id, open_id, token }
      ← { jwt_token, uid }

[Bot] → TCP connect to game server (host:port from lobby response)
[Bot] → Send OpCode 104 (LoginReq) with jwt_token
      ← OpCode 105 (LoginRes) — session established
```

The GSDK endpoint and `app_id` are hardcoded in `libgsdk.so` string table. Extract with:

```bash
strings libgsdk.so | grep "bytegsdk.com"
strings libgsdk.so | grep "app_id"
```

### 2.2 Packet Framing

From `Assembly-CSharp.dll` class `Cc.Thedream.Mmo.Network.MessageCodec`:

```
[ 4 bytes: total_length (LE uint32) ]
[ 2 bytes: opcode        (LE uint16) ]
[ N bytes: protobuf body             ]
```

No encryption observed at the transport layer in the extracted DLL — payload is raw Protobuf.

### 2.3 Python PoC — Send a Packet

```python
import struct, socket

def build_packet(opcode: int, proto_bytes: bytes) -> bytes:
    body = struct.pack("<H", opcode) + proto_bytes
    length = struct.pack("<I", len(body) + 4)
    return length + body

def send_packet(sock: socket.socket, opcode: int, proto_bytes: bytes):
    sock.sendall(build_packet(opcode, proto_bytes))

def recv_packet(sock: socket.socket) -> tuple[int, bytes]:
    header = sock.recv(6)
    total_len, opcode = struct.unpack_from("<IH", header)
    body = sock.recv(total_len - 6)
    return opcode, body
```

### 2.4 Key OpCodes for Automation

| OpCode | Direction | Name (from `MessageId` enum) | Purpose |
|--------|-----------|-------------------------------|---------|
| 104 | C→S | `LoginReq` | Session login |
| 105 | S→C | `LoginRes` | Login confirmation |
| 231 | C→S | `FishingCastReq` | Cast fishing rod |
| 410 | S→C | `FishingResultNtf` | Fish caught notification |
| 43  | C→S | `ShopBuyReq` | Buy item from market |
| 319 | S→C | `ShopItemListNtf` | Market item list push |
| 301 | C→S | `QuestAcceptReq` | Accept daily quest |
| 302 | S→C | `QuestAcceptRes` | Quest accepted |
| 400 | C→S | `RefineReq` | Refine equipment |
| 401 | S→C | `RefineRes` | Refine result |
| 420 | C→S | `EnchantReq` | Start enchantment |
| 421 | S→C | `EnchantRes` | Enchantment result |

### 2.5 Auto Fishing Loop (pseudocode)

```python
FISHING_CAST  = 231
FISHING_RESULT = 410

async def auto_fish(sock, rod_uid: int, bait_id: int):
    while True:
        req = FishingCastReq(rod_uid=rod_uid, bait_id=bait_id)
        send_packet(sock, FISHING_CAST, req.SerializeToString())

        opcode, data = await recv_packet(sock)
        if opcode == FISHING_RESULT:
            result = FishingResultNtf()
            result.ParseFromString(data)
            print(f"Caught: {result.item_id} x{result.item_count}")
        await asyncio.sleep(result.next_cast_delay_ms / 1000)
```

### 2.6 Market Sniper Loop (pseudocode)

```python
MARKET_LIST = 319
MARKET_BUY  = 43

async def snipe_item(sock, target_item_id: int, max_price: int):
    async for opcode, data in stream_packets(sock):
        if opcode == MARKET_LIST:
            listings = ShopItemListNtf()
            listings.ParseFromString(data)
            for item in listings.items:
                if item.item_id == target_item_id and item.price <= max_price:
                    req = ShopBuyReq(listing_uid=item.uid, quantity=1)
                    send_packet(sock, MARKET_BUY, req.SerializeToString())
                    print(f"Sniped {item.item_id} @ {item.price}z")
```

---

## 3. Route B — Frida In-Process Hook

### 3.1 Why Hooking Is Easy Here

`libil2cpp.so` is **completely unstripped** — all `il2cpp_*` runtime exports are in `.dynsym`. This means:
- No need to pattern-scan for offsets.
- Method lookup uses `il2cpp_class_get_method_from_name()` at runtime.
- All managed C# types are accessible via the IL2CPP reflection API.

### 3.2 Verify Exports

```bash
nm -D libil2cpp.so | grep "il2cpp_class_get_method"
# Expected: T il2cpp_class_get_method_from_name
```

### 3.3 Frida Script Template

```javascript
// Attach: frida -U -n "com.gravity.rox" -l hook.js

const il2cpp = {
    getClass:  new NativeFunction(
        Module.findExportByName("libil2cpp.so", "il2cpp_class_from_name"), 'pointer', ['pointer','pointer','pointer']),
    getMethod: new NativeFunction(
        Module.findExportByName("libil2cpp.so", "il2cpp_class_get_method_from_name"), 'pointer', ['pointer','pointer','int']),
    invoke:    new NativeFunction(
        Module.findExportByName("libil2cpp.so", "il2cpp_runtime_invoke"), 'pointer', ['pointer','pointer','pointer','pointer']),
    getDomain: new NativeFunction(
        Module.findExportByName("libil2cpp.so", "il2cpp_domain_get"), 'pointer', []),
    getAssemblies: new NativeFunction(
        Module.findExportByName("libil2cpp.so", "il2cpp_domain_get_assemblies"), 'pointer', ['pointer','pointer']),
};

// Hook fishing result notification handler
function hookFishingResult() {
    // Class: Cc.Thedream.Mmo.Game.FishingModule
    // Method: OnFishingResultNtf(FishingResultNtf msg)
    const domain  = il2cpp.getDomain();
    // ... resolve class ptr via il2cpp_class_from_name("", "FishingModule")
    // ... resolve method ptr via il2cpp_class_get_method_from_name(classPtr, "OnFishingResultNtf", 1)
    // ... Interceptor.attach(methodPtr.add(0x10), { onEnter(args) { ... } })
    console.log("[Hook] FishingResult handler attached");
}

hookFishingResult();
```

> **Note:** The `+ 0x10` offset skips the ARM64 function prologue to land after the stack frame setup. Adjust per function if Frida reports an alignment fault.

### 3.4 Hook: Intercept Refine Result

```javascript
// Target: Cc.Thedream.Mmo.Game.RefineModule.OnRefineRes
Interceptor.attach(refineResMethodPtr, {
    onEnter(args) {
        // args[0] = this (Il2CppObject*)
        // args[1] = RefineRes proto message object
        const successField = args[1].add(OFFSET_success).readU8();
        const newGrade     = args[1].add(OFFSET_new_grade).readU32();
        console.log(`[Refine] success=${successField} newGrade=+${newGrade}`);
    }
});
```

Field offsets for proto message structs are found by dumping `Assembly-CSharp.dll` with `Il2CppDumper` (trim 8-byte prefix from `global-metadata.dat` first).

### 3.5 Anti-Detection Considerations

ByteDance GameProtect (`libhhld-rt.so`) performs:
1. APK signature hash verification via JNI.
2. `/proc/self/maps` scan for injected `.so` paths.
3. `ptrace` self-attach to block debugger attach.

Mitigations (research only):
- Use Frida Gadget embedded mode instead of `frida-server` injection.
- Patch `libhhld-rt.so` ptrace call to `NOP` via `frida --no-pause` before attach.
- Run inside a custom Android emulator image with maps scan bypassed.

---

## 4. Protobuf Schema Reconstruction

Since `.proto` files are not shipped, reconstruct from `Assembly-CSharp.dll` field names:

```bash
# Install ILSpy or use dnSpy on Windows
# Open Assembly-CSharp.dll → namespace Cc.Thedream.Mmo.Protocal
# Each MessageId corresponds to a generated proto class
# Field names and types give the wire schema
```

Example reconstructed schema for `RefineReq` (OpCode 400):

```protobuf
message RefineReq {
    int64  equip_uid          = 1;
    bool   use_protect_item   = 2;
    int32  protect_item_id    = 3;   // 10422012 = Blessed Oridecon
}

message RefineRes {
    int32  result             = 1;   // 0=success, 1=fail, 2=break, 3=downgrade
    int32  new_grade          = 2;
    int64  equip_uid          = 3;
    bool   used_protect       = 4;
}
```

---

## 5. What Automation CAN and CANNOT Do

### Feasible (Client sends valid packets, server executes)

| Automation | OpCode | Effort |
|------------|--------|--------|
| Auto Fishing loop | 231 / 410 | Low — cast → wait → collect |
| Daily Quest auto-accept | 301 / 302 | Low — static quest IDs |
| Market Sniper | 43 / 319 | Medium — parse listing stream |
| Vending stall auto-restock | custom | Medium |
| AOI-based mob approach | 200-series move packets | High — map pathfinding needed |

### Not Feasible (Server-authoritative RNG)

| Action | Why |
|--------|-----|
| Increase refine success rate | Roll computed on server; client only sends `equip_uid` |
| Predict enchant result | `pityCounter` state held server-side |
| Duplicate items | Server validates inventory delta per packet |
| Teleport / speed hack | AOI position validated against last known position |

---

## 6. Quick-Start Checklist

- [ ] Dump `Assembly-CSharp.dll` with dnSpy — verify all `MessageId` values match table in `01-network-and-protocols.md`
- [ ] Trim 8 bytes from `global-metadata.dat` → run `Il2CppDumper` → get full method offset table
- [ ] Capture live traffic with `mitmproxy` (or `tcpdump` on rooted device) to confirm packet framing
- [ ] Reconstruct `.proto` files for target OpCodes using dnSpy field inspection
- [ ] Implement `build_packet` / `recv_packet` helpers (see §2.3)
- [ ] Test Auto Fishing loop in isolated account before broader automation

---

## 7. References

| File | Role |
|------|------|
| [`Assembly-CSharp.dll`](file:///D:/CenNextWorkSpace/Rox/extracted/Assembly-CSharp.dll) | All C# types, `MessageId` enum, proto message classes |
| [`global-metadata.dat`](file:///D:/CenNextWorkSpace/Rox/extracted/global-metadata.dat) | IL2CPP v24 string/type tables (trim 8-byte prefix) |
| [`libil2cpp.so`](file:///D:/CenNextWorkSpace/Rox/extracted/libil2cpp.so) | Unstripped ARM64 runtime — all `il2cpp_*` exports |
| [`01-network-and-protocols.md`](file:///D:/CenNextWorkSpace/Rox/docs/01-network-and-protocols.md) | Full OpCode table and auth flow |
| [`02-equipment-refine-upgrade.md`](file:///D:/CenNextWorkSpace/Rox/docs/02-equipment-refine-upgrade.md) | Refine probability matrix |
| [`03-enchantment-system.md`](file:///D:/CenNextWorkSpace/Rox/docs/03-enchantment-system.md) | Enchant algorithm and pity counter |
| [`05-native-security-and-xlua.md`](file:///D:/CenNextWorkSpace/Rox/docs/05-native-security-and-xlua.md) | Security stack and Frida attack surface |
