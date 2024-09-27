import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import {
  createBrowserRouter,
  RouterProvider
} from 'react-router-dom'


const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />
  },
  {
    path: "/login",
    element: <Login />
  },
  {
    path: "/register",
    element: <Register />,
  },
  {
    path: "/listkarma",
    element: <PrivateRoute element={<FileUploadAndGrid />} />,
  }
]
)

import './App.css'
import Home from './Home/Home'
import Login from './Login/Login'
import Register from './Register/Register'
import PocketBaseProvider from './PocketBaseProvider'
import { PrivateRoute } from './PrivateRoute'
import FileUploadAndGrid from './Components/FileUploadAndGrid'

function App() {

  return (
    <div className='bg-zinc-50' h-max min-h min-h-screen w-full>
      <PocketBaseProvider>
        <RouterProvider router={router} />
      </PocketBaseProvider>
    </div>
  )
}

export default App
