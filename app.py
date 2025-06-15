from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'yoleida_secret_key'

USERS_FILE = 'usuarios.json'
CITAS_FILE = 'citas.json'

def cargar_datos(archivo):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return []

def guardar_datos(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuarios = cargar_datos(USERS_FILE)
        nuevo_usuario = {
            "usuario": request.form['usuario'],
            "contrasena": request.form['contrasena']
        }
        if any(u['usuario'] == nuevo_usuario['usuario'] for u in usuarios):
            flash("Usuario ya existe.")
            return redirect(url_for('registro'))
        usuarios.append(nuevo_usuario)
        guardar_datos(USERS_FILE, usuarios)
        flash("Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuarios = cargar_datos(USERS_FILE)
        user = request.form['usuario']
        pw = request.form['contrasena']

        # Verifica si es el admin
        if user == 'admin' and pw == 'admin':
            session['usuario'] = 'admin'
            session['rol'] = 'admin'  # ✅ Añadido para que funcione
            return redirect(url_for('panel_admin'))

        # Verifica si es un usuario cliente
        for u in usuarios:
            if u['usuario'] == user and u['contrasena'] == pw:
                session['usuario'] = user
                session['rol'] = 'cliente'  # ✅ También puedes guardar rol
                return redirect(url_for('cliente'))

        flash("Credenciales inválidas.")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('rol', None)  # ✅ Esto borra también el rol
    return redirect(url_for('index'))

@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
    if 'usuario' not in session or session['usuario'] == 'admin':
        return redirect(url_for('login'))

    usuario = session['usuario']
    citas = cargar_datos(CITAS_FILE)
    citas_usuario = [c for c in citas if c['usuario'] == usuario]

    if request.method == 'POST':
        fecha_input = request.form['fecha']
        hora_input = request.form['hora']
        servicio = request.form['servicio']

        # Traducción manual de día y mes a español
        dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

        fecha_dt = datetime.strptime(fecha_input, "%Y-%m-%d")
        dia = dias[fecha_dt.weekday()]
        mes = meses[fecha_dt.month - 1]
        fecha_formateada = f"{dia.capitalize()} {fecha_dt.day} de {mes} de {fecha_dt.year}"

        # Convertir hora al formato 12h con AM/PM
        hora_dt = datetime.strptime(hora_input, "%H:%M")
        hora_formateada = hora_dt.strftime("%I:%M %p")

        nueva_cita = {
            "usuario": usuario,
            "fecha": fecha_formateada,
            "hora": hora_formateada,
            "servicio": servicio,
            "estado": "pendiente"
        }

        citas.append(nueva_cita)
        guardar_datos(CITAS_FILE, citas)
        return redirect(url_for('cliente'))

    return render_template('dashboard_cliente.html', usuario=usuario, citas=citas_usuario)

@app.route('/admin')
def panel_admin():
    if session.get('rol') != 'admin':
        return redirect('/login')
    with open('citas.json', 'r') as f:
        citas = json.load(f)
    with open('usuarios.json', 'r') as f:
        usuarios = json.load(f)
    return render_template('dashboard_admin.html', citas=citas, usuarios=usuarios)

@app.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    if session.get('usuario') != 'admin':
        return redirect('/login')
    
    index = int(request.form['index'])
    nuevo_estado = request.form['estado']
    citas = cargar_datos(CITAS_FILE)

    if 0 <= index < len(citas):
        citas[index]['estado'] = nuevo_estado
        guardar_datos(CITAS_FILE, citas)

    return redirect(url_for('panel_admin'))

@app.route('/eliminar_cita', methods=['POST'])
def eliminar_cita():
    if session.get('usuario') != 'admin':
        return redirect('/login')
    
    index = int(request.form['index'])
    citas = cargar_datos(CITAS_FILE)

    if 0 <= index < len(citas):
        citas.pop(index)
        guardar_datos(CITAS_FILE, citas)

    return redirect(url_for('panel_admin'))

if __name__ == '__main__':
    app.run(debug=True)