import { Link } from "react-router-dom";
import "./Menu.css";


export default function Menu(){

return (

<aside className="menu">

<h1>COTILLON</h1>


<Link to="/">🏠 Inicio</Link>

<Link to="/ventas">🛒 Ventas</Link>

<Link to="/productos">📦 Productos</Link>

<Link to="/pedidos">📋 Pedidos</Link>

<Link to="/documentos">📄 Documentos</Link>

<Link to="/carteles">🏷️ Carteles / Ofertas</Link>

<Link to="/clientes">👥 Clientes</Link>

<Link to="/historial">🕘 Historial</Link>

<Link to="/caja">💰 Caja</Link>

<Link to="/reportes">📊 Reportes</Link>

<Link to="/configuracion">⚙️ Configuración</Link>


</aside>

)

}