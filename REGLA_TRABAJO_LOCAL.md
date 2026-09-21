# 🛑 REGLA ABSOLUTA DE DESARROLLO — TRABAJO 100% LOCAL

## ⚠️ PROHIBIDO PUSHEAR A GITHUB O RENDER SIN AUTORIZACIÓN EXPRESA

Para evitar sobrecargar los recursos y minutos de build de Render.com:

1. **TODO EL TRABAJO ES 100% LOCAL**:
   * Todo ajuste de código, pruebas de estrategia, cambios en modelos matemáticos o archivos de estado se realizan **exclusivamente en esta PC local y en la rama dev**.
   * **NUNCA** ejecutar git push origin dev ni git push origin main.
   * **NUNCA** ejecutar deploy.ps1.
   * **NUNCA** hacer requests POST a .render_hook.

2. **ENTORNO DE PRUEBAS LOCAL**:
   * Para probar el sistema y visualizar el dashboard idéntico a Render:
     `powershell
     .\dev_local.ps1
     `
   * El dashboard local se abrirá en: **http://localhost:10000**.
   * Emula al 100% las variables de entorno de Render (PORT=10000, RENDER_EXTERNAL_URL=http://localhost:10000).

3. **SOLO UN PUSH FINAL CUANDO TODO ESTÉ LISTO**:
   * Únicamente cuando el usuario finalice su sesión de trabajo y dé la orden explícita (ej. *'listo, subí todo'*), se procederá a ejecutar el despliegue a producción consolidado mediante:
     `powershell
     .\deploy.ps1
     `

---
*Esta regla aplica tanto al desarrollador como a cualquier agente de Inteligencia Artificial (Antigravity, Cursor, Copilot, etc.) que asista en cualquier PC compartida.*