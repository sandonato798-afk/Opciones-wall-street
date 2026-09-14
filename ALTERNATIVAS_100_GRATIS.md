# Alternativas 100% GRATUITAS para Correr el Bot 24/7 en la Nube

Si querés dejar corriendo el bot de day trading / opciones **sin gastar un solo dólar**, estas son las mejores opciones **100% Gratuitas** (algunas de por vida, otras por 1 año o mediante tareas automatizadas):

---

## 🥇 1. Oracle Cloud "Always Free" (GRATIS DE POR VIDA / 365 días al año)

Oracle Cloud ofrece la **mejor capa gratuita permanente de la industria**. No vence al año ni te exige actualizar a plan de pago.

- **Qué te dan GRATIS de por vida**:
  - **2 servidores VPS Linux** (AMD Compute 1GB RAM) o hasta **4 OCPUs con 24GB RAM** (ARM Ampere).
  - Tráfico y almacenamiento en disco de 200GB sin costo.
- **Por qué es ideal**: Es un servidor VPS propio con IP fija. Instalas Python, corres `python3 daemon_runner.py` con `systemd` y queda operando las **24 horas, los 365 días del año sin apagar jamás**.
- **Cómo registrarse**: En [oracle.com/cloud/free](https://www.oracle.com/cloud/free/), creas la cuenta eligiendo la opción "Always Free Eligible".

---

## 🥈 2. AWS EC2 (Capa Gratuita de Amazon Web Services por 12 Meses)

Amazon AWS te regala un servidor VPS Linux completo durante 1 año.

- **Qué te dan GRATIS**: 750 horas al mes (equivalente a 24 horas al día, los 31 días del mes) de un servidor `t2.micro` o `t3.micro` durante **12 meses**.
- **Cómo usarlo**:
  1. Registras una cuenta en [aws.amazon.com](https://aws.amazon.com).
  2. Creas una instancia **EC2 Ubuntu** en la capa "Free Tier".
  3. Ejecutas `python3 daemon_runner.py` en segundo plano.

---

## 🥉 3. GitHub Actions Workflows (Cron Automático 100% Gratis)

Si no querés usar un servidor continuo, podés hacer que **GitHub ejecute tu bot gratis cada 5 o 15 minutos** durante el horario de Wall Street mediante un script de automatización ("Cron Job").

- **Qué te dan GRATIS**: 2,000 minutos de ejecución al mes en cualquier repositorio de GitHub.
- **Cómo funciona**:
  - Creás un archivo `.github/workflows/daytrade_bot.yml` en tu repositorio.
  - GitHub enciende un servidor Python cada 5 minutos de 10:30 a 17:00 hs AR, ejecuta `python daytrade_options_bot.py`, registra las señales/operaciones y guarda el resultado.
- **Ventaja**: Cero mantenimiento de servidores, cero tarjetas de crédito o vencimientos.

---

## 🚀 4. Koyeb / Northflank (Micro-Contenedores 24/7 Siempre Activos)

A diferencia de Render o Heroku, **Koyeb** y **Northflank** ofrecen instancias micro que **NUNCA duermen** en su plan gratuito.

- **Koyeb Free Tier**: 1 servicio Nano gratis de por vida (512MB RAM) que corre `python daemon_runner.py` sin pausarse.
- **Northflank**: 2 servicios micro gratuitos de por vida.
- **Cómo registrarse**: En [koyeb.com](https://www.koyeb.com) o [northflank.com](https://northflank.com).

---

## 🐍 5. PythonAnywhere (Plan Free sin Tarjeta de Crédito)

- **Qué te dan GRATIS**: Una cuenta en [PythonAnywhere.com](https://www.pythonanywhere.com) sin ingresar tarjeta de crédito.
- **Cómo usarlo**: Creás un **Scheduled Task** diario u horario que ejecute `python3 daytrade_options_bot.py`.
- **Ventaja**: Extremadamente fácil de usar. Subís tus archivos `.py` desde el navegador y programás la hora de ejecución.

---

## 📊 Tabla Comparativa de Opciones Gratuitas

| Plataforma | Modalidad Gratis | Duración | Requiere Tarjeta | Ideal Para... |
| :--- | :--- | :--- | :--- | :--- |
| **Oracle Cloud** | VPS 24/7 Dedicado | **GRATIS DE POR VIDA** | Sí (para verificar ID) | **El mejor servidor 24/7 ilimitado** 🏆 |
| **AWS EC2** | VPS 24/7 Dedicado | **12 Meses Gratis** | Sí (para verificar ID) | Servidor profesional Amazon 🌟 |
| **GitHub Actions** | Cron cada 5-15 min | **GRATIS DE POR VIDA** | **NO** | Escaneos programados sin servidor ⚡ |
| **Koyeb** | Background Service | **GRATIS DE POR VIDA** | **NO** | Bot 24/7 sin dormirse 🚀 |
| **PythonAnywhere** | Scheduled Task | **GRATIS DE POR VIDA** | **NO** | Escaneos diarios sin tarjeta 🐍 |
