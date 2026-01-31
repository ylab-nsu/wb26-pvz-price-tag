import { useState } from "react"
import Login from "./pages/Login"
import Home from "./pages/Home"

export default function App() {
    const [auth, setAuth] = useState(false)

    if (!auth) {
        return <Login onSuccess={() => setAuth(true)} />
    }

    return <Home />
}
