# Flujo de Trabajo Git — Opciones Wall Street

## 🔴 REGLA ABSOLUTA
**Nunca se pushea directamente a `main`.**
`main` = Producción = Lo que corre en Render con dinero real.

---

## Ramas

| Rama | Propósito |
|---|---|
| `dev` | Desarrollo diario. Todos los cambios van acá. |
| `main` | Producción. Solo se toca via `deploy.ps1`. |

---

## Comandos del día a día

### Iniciar sesión de desarrollo
```powershell
git checkout dev          # asegurarse de estar en dev
.\dev_local.ps1           # arrancar servidor local en puerto 10000
```

### Durante el desarrollo
```powershell
git add .
git commit -m "feat: descripcion del cambio"
# NO hacer git push — trabajar localmente
```

### Cuando el código está listo para producción
```powershell
.\deploy.ps1              # mergea dev→main, push UNO a Render, vuelve a dev
```

---

## Scripts disponibles

| Script | Función |
|---|---|
| `.\dev_local.ps1` | Servidor local en `http://localhost:10000` emulando Render |
| `.\deploy.ps1` | Deploy a producción (1 push = 1 build en Render) |

---

## Protecciones activas

- **Git Hook pre-push:** Bloquea físicamente cualquier `git push` estando en `main`
- **`deploy.ps1`:** Valida que el código Python sea válido antes de pushear
- **Auto-Deploy de Render:** Desactivar manualmente en el panel de Render → Settings → Auto-Deploy: OFF

---

## Cuánto consume cada hábito

| Hábito | Minutos de Render/mes |
|---|---|
| Push por cada cambio (antes) | ~500 min (límite) |
| Un push por sesión con `deploy.ps1` | ~20-30 min |
