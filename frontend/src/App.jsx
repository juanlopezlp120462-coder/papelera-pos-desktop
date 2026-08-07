import { BrowserRouter, Routes, Route } from "react-router-dom";

import Menu from "./components/menu";

import Inicio from "./pages/Inicio";
import Ventas from "./pages/Ventas";
import Productos from "./pages/Productos";
import Clientes from "./pages/Clientes";
import Caja from "./pages/Caja";
import Reportes from "./pages/Reportes";
import Configuracion from "./pages/Configuracion";
import Pedidos from "./pages/Pedidos";
import Historial from "./pages/Historial";
import Documentos from "./pages/Documentos";
import Carteles from "./pages/Carteles";

import "./App.css";


function App(){

return (

<BrowserRouter>

<div style={{display:"flex"}}>

<Menu />

<main style={{flex:1,padding:20}}>

<Routes>

<Route path="/" element={<Inicio />} />

<Route path="/ventas" element={<Ventas />} />

<Route path="/productos" element={<Productos />} />

<Route path="/clientes" element={<Clientes />} />

<Route path="/caja" element={<Caja />} />

<Route path="/reportes" element={<Reportes />} />

<Route path="/configuracion" element={<Configuracion />} />

<Route path="/pedidos" element={<Pedidos />} />

<Route path="/historial" element={<Historial />} />

<Route path="/documentos" element={<Documentos />} />

<Route path="/carteles" element={<Carteles />} />

</Routes>

</main>

</div>

</BrowserRouter>

)

}


export default App;