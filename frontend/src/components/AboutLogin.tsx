/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the authentication  for the application using Microsoft Azure Active Directory(entraID)
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: February 4, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/

//Imported Libraries
import React, {useEffect} from "react";
// import { useNavigate } from "react-router-dom";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./authConfigur.ts";
// import { loginRequest } from "./authConfigur";
// import './layout.css';
import '../components/Smart-Recruitment/smartrecruitment.css'

const Auth: React.FC = () => {
    // const navigate = useNavigate(); // Variable assigned to useNavigate() function to navigate to a selected page
    const { instance, accounts } = useMsal(); // Variable assigned to useMsal() function to use the instance of the MSAL library

    // const [booleanPairs, setBooleanPairs] = useState([]);
    // const [userInfo, setUserInfo] = useState<{ firstName: string, lastName: string, email: string } | null>(null);

    // const getMachineName = () => {
    //     return new Promise((resolve, reject) => {
    //         try{
    //             const hostname = window.location.hostname
    //             console.log("User's machine hostname is: ", hostname)
    //             resolve(hostname);
    //         } catch(error){
    //             reject(error);
    //         }
    //     })
    // }

    useEffect(() => {
        const handleRedirect = async () => {
          try {
            await instance.initialize();
            const response = await instance.handleRedirectPromise();
            if (response) {
              instance.setActiveAccount(response.account);
              window.location.href = `${window.location.origin}/AboutUs/Login/Smart-Recruitment`; // Redirect after login
            } else {
              const activeAccount = instance.getActiveAccount();
              if (!activeAccount && accounts.length > 0) {
                instance.setActiveAccount(accounts[0]);
              }
            }
          } catch (error) {
            console.error("Error handling redirect", error);
          }
        };
    
        handleRedirect();
    }, [accounts, instance]);


    // const collectUserInfo = async (response: any, accessToken: string, idToken: string, status: string) => {
    //     const idTokenClaims = response.idTokenClaims as any;
    //     const firstName = idTokenClaims.given_name || idTokenClaims.name?.split(' ')[0];
    //     const lastName = idTokenClaims.family_name || idTokenClaims.name?.split(' ').slice(1).join(' ');
    //     const email = idTokenClaims.email;
    //     const sub = idTokenClaims.sub;

    //     console.log(`User logged in: ${firstName} ${lastName}, Email: ${email}, Sub: ${sub}`);

    //     // Set the active account for future token acquisition
    //     instance.setActiveAccount(response.account);

    //     const machineName = await getMachineName();

    //     // console.log(`Sending user info to server: Username: ${firstName} ${lastName}, Email: ${email}, Machine Name: ${machineName}`);

    //     fetch(`${process.env.REACT_APP_BACKEND_URL}/userLoginInfo`, {
    //         method: 'POST',
    //         headers: {
    //             'Content-Type': 'application/json',
    //             Authorization: `Bearer ${accessToken}`,
    //             Authentication: `Bearer ${idToken}`
    //         },
    //         body: JSON.stringify({
    //             username: `${firstName} ${lastName}`,
    //             email: email,
    //             machineName: machineName,
    //             sub: sub,
    //             status: status
    //         })
    //     }).then(response => response.json())
    //         .then(data => console.log('User info sent to server:', data))
    //         .catch(error => console.error('Error sending user info to server:', error));
    // };

    // const getIpAddress = async (): Promise<string | null> => {
    //     try {
    //         const response = await fetch('https://api.ipify.org?format=json');
    //         const data = await response.json();
    //         console.log("IPV4 Address: ", data.ip)
    //         return data.ip;
    //     } catch (error) {
    //         console.error('Error fetching IP address:', error);
    //         return null;
    //     }
    // };

    const collectUserInfo = async (response: any, accessToken: string, idToken: string) => {
        const idTokenClaims = response.idTokenClaims as any;
        const firstName = idTokenClaims.given_name || idTokenClaims.name?.split(' ')[0];
        const lastName = idTokenClaims.family_name || idTokenClaims.name?.split(' ').slice(1).join(' ');
        const email = idTokenClaims.email;
        const sub = idTokenClaims.sub;
        // const ipAddress = await getIpAddress();
    
        console.log(`User logged in: ${firstName} ${lastName}, Email: ${email}, Sub: ${sub}`);
    
        // Set the active account for future token acquisition
        instance.setActiveAccount(response.account);
    
        // const machineName = await getMachineName();
        
        const userInfoResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/userInfo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${accessToken}`,
                Authentication: `Bearer ${idToken}`
            },
            body: JSON.stringify({
                username: `${firstName} ${lastName}`,
                email: email,
                sub: sub,
                // ipAddress: ipAddress
            })
        });

        const userInfoData = await userInfoResponse.json();
        
        let userInfoId;
        let sessionId;
    
        if (userInfoResponse.status === 409) {
            console.log('User already exists:', userInfoData.existingUser);
            userInfoId = userInfoData.existingUser.USERINFOID;
            sessionId = userInfoData.newSession.SESSIONID; // Ensure the session ID is returned even if the user already exists
        } else {
            userInfoId = userInfoData.userInfo.USERINFOID;
            sessionId = userInfoData.newSession.SESSIONID;
        }
    
        if (!userInfoId) {
            console.error('USERINFOID is missing');
            return;
        }

        if (!sessionId){
            console.error('SessionID is missing');
            return;
        }
    
        // Store the session ID in sessionStorage
        sessionStorage.setItem('sid', sessionId);
    
        console.log('User info and session details stored:', userInfoData);
    };

    const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        const activeAccount = instance.getActiveAccount();
        if (activeAccount) {
            console.log("User already logged in:", activeAccount);
            const tokenResponse = await instance.acquireTokenSilent({
                ...loginRequest,
                account: activeAccount || undefined
            });
            const accessToken = tokenResponse.accessToken;
            const idToken = tokenResponse.idToken;
            await collectUserInfo({ account: activeAccount, idTokenClaims: activeAccount.idTokenClaims }, accessToken, idToken);
            window.location.href = `${window.location.origin}/AboutUs/Login/Smart-Recruitment`; // Use window.location.href for navigation
            return;
        }

        instance.loginPopup(loginRequest).then(async (response) => {
            if (response) {
                const tokenResponse = await instance.acquireTokenSilent({
                    ...loginRequest,
                    account: response.account || undefined
                });
                const accessToken = tokenResponse.accessToken;
                const idToken = tokenResponse.idToken;
                await collectUserInfo(response, accessToken, idToken);
                window.location.href = `${window.location.origin}/AboutUs/Login/Smart-Recruitment`; // Use window.location.href for navigation
            }
        }).catch((error) => {
            console.error("Was not able to log in", error);
        });
    };

    // const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    //     e.preventDefault();
        
    //     // Check if there is already an active account
    //     const activeAccount = instance.getActiveAccount();
    //     if (activeAccount) {
    //         console.log("User already logged in:", activeAccount);
    //         window.location.href = `${window.location.origin}/AboutUs/Login/Smart-Recruitment`; // Use window.location.href for navigation
    //         return;
    //     }

    //     // Proceed with loginPopup if no active account
    //     instance.loginPopup(loginRequest).then(async (response) => {
    //         if (response) {
    //             const idToken = response.idTokenClaims as any;
    //             const firstName = idToken.given_name || idToken.name?.split(' ')[0];
    //             const lastName = idToken.family_name || idToken.name?.split(' ').slice(1).join(' ');
    //             const email = idToken.email;

    //             console.log(`User logged in: ${firstName} ${lastName}, Email: ${email}`);

    //             // Set the active account for future token acquisition
    //             instance.setActiveAccount(response.account);

    //             const machineName = await getMachineName();

    //             fetch(`${process.env.REACT_APP_BACKEND_URL}/userLoginInfo`, {
    //                 method: 'POST',
    //                 headers: {
    //                     'Content-Type': 'application/json'
    //                 },
    //                 body: JSON.stringify({
    //                     username: `${firstName} ${lastName}`,
    //                     email: email,
    //                     machineName: machineName
    //                 })
    //             }).then(response => response.json())
    //               .then(data => console.log('User info sent to server:', data))
    //               .catch(error => console.error('Error sending user info to server:', error));

    //             // Navigate to the desired page
    //             window.location.href = `${window.location.origin}/AboutUs/Login/Smart-Recruitment`; // Use window.location.href for navigation
    //         }
    //     }).catch((error) => {
    //         console.error("Was not able to log in", error);
    //     });
    // };

    return (
        <section className="auth-section">
            <div className="auth-container">
                    
                {/* Logo */}
                <div className="auth-logo">
                    <img src="/assets/images/mzm_logo.png" alt="MZM Technologies" />
                </div>
                    
                {/* Login functionality displayed */}
                <form onSubmit={handleLogin} className="auth-form">
                    <p>Please Login to Your Account</p>

                    {/* Submit button */}
                    <div className="auth-button-container">
                        <button
                            className="auth-button"
                            type="submit"
                        >
                            Log in with Microsoft
                        </button>
                    </div>
                </form>
            </div>
        </section>
    );
}

export default Auth;
