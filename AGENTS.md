# 🛑 DIRECTIVAS PARA AGENTES DE INTELIGENCIA ARTIFICIAL

## REGLA OPERATIVA FUNDAMENTAL: TRABAJO 100% LOCAL (RAMA DEV)

Cualquier agente de IA que opere en este repositorio (en esta PC o en otra máquina sincronizada por Dropbox) DEBE CUMPLIR ESTRICTAMENTE:

1. **NO HACER PUSH A GITHUB NI A RENDER**:
   * Queda terminantemente prohibido ejecutar git push, llamar al script deploy.ps1 o invocar el Deploy Hook de Render por cada cambio menor o iteración.
   * Render Free Tier tiene cuotas mensuales estrictas de minutos de build que no deben ser consumidas innecesariamente.

2. **TRABAJAR EXCLUSIVAMENTE EN LOCAL**:
   * Trabajar siempre en la rama dev.
   * Para probar el sistema, levantar el servidor local mediante:
     `powershell
     .\dev_local.ps1
     `
   * Acceder al panel de pruebas local en http://localhost:10000.

3. **PUSH CONSOLIDADO ÚNICO**:
   * Solo hacer push si el usuario lo ordena de manera inequívoca y explícita (ej. 'deploya a render', 'hace el push a produccion').

4. **ESTRUCTURA DEL SISTEMA**:
   * Consultar siempre CONTEXT_HANDOFF.md para conocer el estado actual de las 4 capas, colateral y métricas de NAV.