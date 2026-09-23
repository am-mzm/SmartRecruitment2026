/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the protected routes for the application using React Router Dom and useAuth.ts
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: February 4, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
import React, {useState, useEffect} from "react";
import { Route, Navigate } from "react-router-dom";
// import useAuth from '../useAuth';
import useAuth from '../useAuth.ts'

const ProtectedRoute = ({ element: Component }: {element: React.ReactElement}) => {
    const isAuthenticated = useAuth();
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    useEffect(() => {
        const handleLogout = () => {
            setIsLoggingOut(true);
        }

        window.addEventListener("logout", handleLogout);

        return () => {
            window.removeEventListener("logout", handleLogout);
        }
    }, [])

    if (isLoggingOut) {
        return Component
    }
    
    return isAuthenticated ? Component : <Navigate to="/AboutUs/Login" />
}

export default ProtectedRoute
