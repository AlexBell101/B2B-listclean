import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

import Header from './Header/Header'
import Home from './Home/Home'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <Header></Header>
      </div>
      <Home></Home>
    </>
  )
}

export default App
