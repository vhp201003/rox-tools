# 07 — Butterfly Quest Navigation System

> **Scope:** Toàn bộ tính năng "Click Butterfly → Teleport đến Quest" trong Ragnarok X.  
> Dữ liệu từ static analysis `Assembly-CSharp.dll` (8.11 MB), string heap parsing, và binary symbol extraction.

---

## 1. Tổng Quan Tính Năng

Mỗi quest trong ROX hiển thị **biểu tượng bướm** (butterfly icon) bên cạnh mục tiêu nhiệm vụ. Khi người dùng click, client thực hiện một trong hai hành động:

| Tình huống | Hành động |
|-----------|-----------|
| Quest objective **cùng map** | Auto-path movement (chỉ gửi `ClientStartMoveRequest`) |
| Quest objective **khác map / scene** | Gửi `ClientTaskTeleportRequest` → server teleport player |

Ngoài ra có một loại teleport thứ hai: **Wing Teleport** (`WTeleport`) — dùng **Butterfly Wing item** để teleport về thị trấn / điểm đã ghé thăm.

---

## 2. Các Packet Liên Quan (Xác Nhận Từ DLL)

### 2.1 Client → Server (C→S)

| Tên class | Mô tả | Ghi chú |
|-----------|-------|---------|
| `ClientTaskTeleportRequest` | **Chính** — click butterfly trên quest để nhảy đến scene mục tiêu | Payload: `task_id`, `target_scene_id`, `target_npc_id` |
| `ClientWTeleportRequest` | **Wing Teleport** — dùng Butterfly Wing item | Payload: `target_teleport_mark` |
| `ClientOnTeleporterRequest` | Bước vào warp gate / portal trong scene | Payload: `teleporter_id` |
| `ClientTeleportByNpcRequest` | NPC offer teleport (VD: Kafra) | Payload: `npc_id`, `target_scene_id` |
| `ClientTeleportByTask` | Variant của task teleport (không có Request suffix) | Có thể là internal wrapper |
| `ClientOnTeleporterInPronteraRaidSceneRequest` | Teleporter đặc biệt trong Prontera Raid scene | Specific to raid content |

### 2.2 Server → Client (S→C)

| Tên class | Mô tả |
|-----------|-------|
| `ToClientTeleportNotify` | Server xác nhận teleport thành công — client load scene mới |
| `ToClientWTeleportResponse` | Server response cho Wing Teleport request |
| `OnServerTeleportConfirmed` | Internal event fired sau khi server confirm |

---

## 3. Client-Side Architecture

```
[Player clicks butterfly icon on quest UI]
           │
           ▼
   QuestModule.OnButterflyClick()
           │
           ├─► [Same scene?] → TeleporterModel.StartAutoPath(target_x, target_z)
           │                        └─► gửi ClientStartMoveRequest packets (opcode 5)
           │
           └─► [Different scene] → TeleporterModel.DoTeleport(task_id, scene_id)
                                        └─► encode ClientTaskTeleportRequest
                                        └─► NetClient.Send(packet)
```

### Key Client Classes

| Class | Vai trò |
|-------|---------|
| `TeleporterModel` | Business logic: quyết định loại teleport nào cần dùng |
| `TeleporterEntity` | Game world entity đại diện cho warp gate vật lý |
| `TeleporterManager` | Singleton quản lý toàn bộ teleporter trong scene |
| `TeleportSceneModel` | Config data: scene_id, spawn coordinates, requirements |
| `TeleportSceneInfo` | Info cho một destination (by scene ID) |
| `TeleportSceneInfoByNpcId` | Info cho destination (by NPC ID) |
| `SceneTeleporterInfo` | Metadata của teleporter object trong scene |
| `DreamGameTeleporterManagerWrap` | C++ engine wrapper cho TeleporterManager |
| `DreamGameTeleporterEntityWrap` | C++ engine wrapper cho TeleporterEntity |

### Key Methods (Từ String Heap)

| Method | Mô tả |
|--------|-------|
| `GetTeleporterInScene(scene_id)` | Lấy teleporter entity trong scene hiện tại |
| `GetTeleporterInSceneByArea(area_id)` | Lấy teleporter theo area |
| `GetTeleportSceneInfoById(scene_id)` | Lấy config cho một scene destination |
| `GetTeleportSceneInfoByNpcId(npc_id)` | Lấy config cho destination qua NPC |
| `GetTeleportNpcInScene()` | Lấy danh sách NPC có khả năng teleport trong scene |
| `InitTeleporterInScene()` | Khởi tạo teleporter entities khi load scene |
| `CheckTeleportActive(teleporter_id)` | Kiểm tra teleporter có đang active không |
| `CheckTeleportNodeRearched()` | Kiểm tra đã từng đến node destination chưa |
| `DoTeleport(...)` | Thực hiện teleport (internal) |
| `StartTeleport()` | Begin teleport animation + send packet |
| `OnBeforeTeleport()` | Pre-teleport hook (cleanup, save position) |
| `TrySyncServerTeleport()` | Đồng bộ state với server sau teleport |
| `OnOwnerTeleport()` | Handler cho pet/mercenary follow owner teleport |

---

## 4. Wing Teleport (WTeleport) — Butterfly Wing Item

`WTeleport` là hệ thống riêng biệt dành cho item **Butterfly Wing** (cánh bướm tiêu hao):

```
[Player uses Butterfly Wing item]
           │
           ▼
   ItemModule.UseItem(butterfly_wing_id)
           │
           ▼
   TeleporterModel.RequestWTeleport(target_mark)
           │
           ▼
   ClientWTeleportRequest {
       target_teleport_mark: <TeleportMark enum value>,
       last_wteleport_timestamp: <unix timestamp>
   }
           │
           ▼
   Server validates cooldown → ToClientWTeleportResponse
```

**Lỗi có thể nhận về:**
- `WTeleportNotAllowed` — đang ở dungeon không cho phép wing teleport
- `CantTeleportToNeverBeenToScene` — chưa từng đến scene đích
- `CanNotTeleportByServant` — đang điều khiển servant không thể teleport

---

## 5. Kịch Bản Automation

### 5.1 Auto Quest Navigation (Same Scene)

Client-side only — không cần packet đặc biệt nào ngoài move:

```python
# Lấy quest objective coordinates từ QuestAllNotify (S→C)
# Rồi gửi move packets đến tọa độ đó
def navigate_to_quest_objective(quest_id: int, target_x: float, target_z: float):
    req = ClientStartMoveRequest(
        target_x=target_x,
        target_z=target_z,
        move_type=MoveType.AUTO_PATH
    )
    send_packet(sock, OPCODE_START_MOVE, req.SerializeToString())
```

### 5.2 Auto Task Teleport (Cross-Scene)

```python
TASK_TELEPORT_REQ = ...  # OpCode cần xác nhận bằng dnSpy

def teleport_to_quest_scene(task_id: int, scene_id: int):
    req = ClientTaskTeleportRequest()
    req.task_id  = task_id
    req.scene_id = scene_id
    send_packet(sock, TASK_TELEPORT_REQ, req.SerializeToString())
    
    # Đợi ToClientTeleportNotify để biết scene load xong
    opcode, data = recv_packet(sock)
    if opcode == TO_CLIENT_TELEPORT_NOTIFY:
        notify = ToClientTeleportNotify()
        notify.ParseFromString(data)
        print(f"Teleported to scene: {notify.scene_id} at ({notify.spawn_x}, {notify.spawn_z})")
```

### 5.3 Daily Mission Automation Full Flow

```
1. Recv QuestBoardInfoResponse  → danh sách mission_id
2. Send ClientTaskAccept         → nhận mission
3. Check mission type:
   - Kill quest   → combat loop (Approach 3: Frida hook)
   - Talk to NPC  → Send ClientTaskTeleportRequest → move to NPC → ClientInteractNpcRequest
   - Collect item → market sniper OR combat loop
4. Send ClientTaskFinish         → nhận reward
5. Repeat
```

---

## 6. Opcode Numbers — Trạng Thái Xác Nhận

> **Lưu ý:** Các số OpCode bên dưới cần xác nhận bằng dnSpy/ILSpy do giới hạn binary parsing từ raw .NET PE metadata. Tên class đã được xác nhận 100% từ string heap.

| Packet class | Opcode (cần xác nhận) | Cách xác nhận |
|---|---|---|
| `ClientTaskTeleportRequest` | ~300 (từ byte context) | dnSpy → `MessageId.CLIENT_TASK_TELEPORT_REQUEST` |
| `ClientWTeleportRequest` | ~297 | dnSpy → `MessageId.CLIENT_W_TELEPORT_REQUEST` |
| `ClientOnTeleporterRequest` | ~20 (từ doc cũ) | Đã verify |
| `ClientTeleportByNpcRequest` | ~296 | dnSpy → `MessageId.CLIENT_TELEPORT_BY_NPC_REQUEST` |
| `ToClientTeleportNotify` | ~309 | dnSpy → `MessageId.TO_CLIENT_TELEPORT_NOTIFY` |
| `ToClientWTeleportResponse` | ~303 | dnSpy → `MessageId.TO_CLIENT_W_TELEPORT_RESPONSE` |

**Cách xác nhận nhanh nhất:**
```
1. Mở dnSpy → File → Open → Assembly-CSharp.dll
2. Search: Cc.Thedream.Mmo.Protocal → MessageId enum
3. Tìm: CLIENT_TASK_TELEPORT_REQUEST → đọc integer value bên phải
```

---

## 7. Prototype Frida Hook — Intercept Task Teleport

```javascript
// Hook TeleporterModel.DoTeleport để log mỗi khi player teleport qua quest
// Targets: libil2cpp.so (unstripped, 231 exports available)

const DoTeleport = il2cpp.getMethod(
    il2cpp.getClass(domainPtr, "Cc.Thedream.Mmo.Game", "TeleporterModel"),
    "DoTeleport", -1  // -1 = any overload
);

Interceptor.attach(DoTeleport.add(0x10), {
    onEnter(args) {
        // args[1] = task_id (Int32)
        // args[2] = scene_id (Int32)
        const taskId  = args[1].toInt32();
        const sceneId = args[2].toInt32();
        console.log(`[Teleport] task=${taskId} → scene=${sceneId}`);
        
        // To automate: call this method programmatically
        // il2cpp.invoke(DoTeleport, thisPtr, [task_id_obj, scene_id_obj], null)
    }
});
```

---

## 8. References

| File | Liên kết |
|------|---------|
| `Assembly-CSharp.dll` | [`extracted/Assembly-CSharp.dll`](file:///D:/CenNextWorkSpace/Rox/extracted/Assembly-CSharp.dll) |
| `06-automation-engineering-guide.md` | [`docs/06-automation-engineering-guide.md`](file:///D:/CenNextWorkSpace/Rox/docs/06-automation-engineering-guide.md) |
| `04-gameplay-subsystems.md` | [`docs/04-gameplay-subsystems.md`](file:///D:/CenNextWorkSpace/Rox/docs/04-gameplay-subsystems.md) |
| `01-network-and-protocols.md` | [`docs/01-network-and-protocols.md`](file:///D:/CenNextWorkSpace/Rox/docs/01-network-and-protocols.md) |
