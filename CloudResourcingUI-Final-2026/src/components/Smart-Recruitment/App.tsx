/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the homepage application component with the form for recruiters to input the job title and description
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: February 4th, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
//Imported Libraries
import React, { useState, useEffect } from 'react'
import { useMsal } from '@azure/msal-react';
// import { useNavigate } from 'react-router-dom';
import JobForm from './JobForm.tsx';
import TechRequirements from './TechRequirements.tsx';
import BooleanString from './BooleanString.tsx';
// import HistoryRecords from './HistoryRecords.tsx';
import './smartrecruitment.css';
import ExperienceSection from './Experience.tsx';
import { loginRequest } from "../authConfigur.ts";
import { TechnologyRequirement, HistoryRecord } from './type.ts';
// import {htmlToText} from 'html-to-text';
// import { InteractionRequiredAuthError } from "@azure/msal-browser";
// import { loginRequest } from '../authConfigur'
// import { callMsGraph } from '../graph.ts';

// Interface for the experience object
interface ExperienceDetails{ // Interface for the experience object
  from: string;
  to: string;
}

// Interface for the technology requirements object
// interface TechnologyRequirement{
//   BOOLEANNAMEVALUEPAIRID?: number;
//   BOOLEANNAME: string;
//   BOOLEANVALUE: string;
//   weightage?: string;
//   isEditable?: boolean;
//   index: number;
// }

// interface HistoryRecord {
//   jobTitle: string;
//   jobDescription: string;
//   booleanPhrase: string;
//   technologyRequirements: TechnologyRequirement[];
// }

// Interface for the boolean pair object
interface BooleanPair{ // Interface for the boolean pair object
  BOOLEANNAMEVALUEPAIRID: number;
  BOOLEANNAME: string;
  BOOLEANVALUE: string;
}

const App: React.FC = () => {
  const [jobTitle, setJobTitle] = useState(''); // State for the job title
  const [description, setDescription] = useState(''); // State for the job description
  const [experience, setExperience] = useState<ExperienceDetails>({ from: '', to: '' }); // State for the experience
  const [parsedKeyTitle, setParsedKeyTitle] = useState(''); // State for the parsed key title
  const [technologyRequirements, setTechnologyRequirements] = useState<TechnologyRequirement[]>([]); // State for the technology requirements
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false); // State for the form submission status
  const [booleanPairs, setBooleanPairs] = useState<BooleanPair[]>([]); // State for the boolean pairs
  const [userInfo, setUserInfo] = useState<{ firstName: string, lastName: string, email: string } | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [jobCode, setJobCode] = useState<string>('')
  const [booleanPhrase, setBooleanPhrase] = useState<string>('')
  const [jobUrl, setJobUrl] = useState<string>('');
  const [authToken, setAuthToken] = useState<string>('');
  const [weightageStored, setWeightageStored] = useState<{value: number, isChanged: boolean}[]>([]);
  const [nameStored, setNameStored] = useState<string[]>([]);
  const [mergedArray, setMergedArray] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string>('');
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [recentHistory, setRecentHistory] = useState<HistoryRecord[]>([]);
  const [processedString, setProcessedString] = useState<string>("");
  const [searchVisible, setSearchVisible] = useState<boolean>(false);
  const [poolValue, setPoolValue] = useState<number>(750);
  const [searchByParameter, setSearchByParameter] = useState<string>("Boolean Name")
  const [toggleParameters, setToggleParameters] = useState<boolean>(false);
  const [toggleJobTitle, setToggleJobTitle] = useState<boolean>(false);
  // const [weightages, setWeightages] = useState<{value: number, isChanged: boolean}[]>([]);

  const { instance, accounts } = useMsal();
  // const navigate = useNavigate();

  // Mapping of job titles to experience levels
  const keytitlesMapping = {
    Junior: { from: '4', to: '5' },
    Intermediate: { from: '6', to: '9' },
    Senior: { from: '10', to: '25' },
  };

  const groupIdToRoleMap: { [key: string]: string } = {
    [process.env.REACT_APP_GROUP_BOOLEAN_MODIFIER_ID as string]: "Boolean_Modifier",
    [process.env.REACT_APP_GROUP_BOOLEAN_READER_ID as string]: "Boolean_Reader"
  };

  // useEffect(() => {
  //   const handleRedirect = async () => {
  //     try {
  //       await instance.initialize();
  //       const response = await instance.handleRedirectPromise();
  //       if (response) {
  //         instance.setActiveAccount(response.account);
  //       } else {
  //         const activeAccount = instance.getActiveAccount();
  //         if (!activeAccount && accounts.length > 0) {
  //           instance.setActiveAccount(accounts[0]);
  //         }
  //       }
  //     } catch (error) {
  //       console.error("Error handling redirect", error);
  //     }
  //   };

  //   handleRedirect();
  // }, [accounts, instance]);
  
  // const getMachineName = () => {
  //   return new Promise((resolve, reject) => {
  //     try {
  //       const hostname = window.location.hostname;
  //       resolve(hostname);
  //     } catch (error) {
  //       reject(error);
  //     }
  //   });
  // };

  // const collectUserInfo = async (idTokenClaims: any, accessToken: string, idToken: string, status: string) => {
  //   const firstName = idTokenClaims.given_name || idTokenClaims.name?.split(' ')[0];
  //   const lastName = idTokenClaims.family_name || idTokenClaims.name?.split(' ').slice(1).join(' ');
  //   const email = idTokenClaims.email || idTokenClaims.preferred_username;
  //   const sub = idTokenClaims.sub;

  //   console.log(`User logged in: ${firstName} ${lastName}, Email: ${email}`);

  //   // Get machine name
  //   const machineName = await getMachineName();

  //   // Log the information before sending it to the server
  //   // console.log(`Sending user info to server: Username: ${firstName} ${lastName}, Email: ${email}, Machine Name: ${machineName}, Status: ${status}`);

  //   // Send user info to the server
  //   fetch(`${process.env.REACT_APP_BACKEND_URL}/userLoginInfo`, {
  //     method: 'POST',
  //     headers: {
  //       'Content-Type': 'application/json',
  //       Authorization: `Bearer ${accessToken}`,
  //       Authentication: `Bearer ${idToken}`
  //     },
  //     body: JSON.stringify({
  //       username: `${firstName} ${lastName}`,
  //       email: email,
  //       machineName: machineName,
  //       sub: sub,
  //       status: status
  //     })
  //   }).then(response => response.json())
  //     .then(data => console.log('User info sent to server:', data))
  //     .catch(error => console.error('Error sending user info to server:', error));
  // };

  const getIpAddress = async (): Promise<string | null> => {
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        console.log("IPV4 Address: ", data.ip)
        return data.ip;
    } catch (error) {
        console.error('Error fetching IP address:', error);
        return null;
    }
  };

  useEffect(() => { // Renders the fetchBooleanPairs function
    const fetchBooleanPairs = async () => { // Function to fetch the boolean pairs from the backend server("http://localhost:3000/booleanPairs")
      try {
        const activeAccount = instance.getActiveAccount() // Gets the active account
        if(!activeAccount){
          throw new Error(`${process.env.REACT_APP_ERROR_MESSAGE_NOACTIVEACCOUNT}`)
        }
        console.log(`${process.env.REACT_APP_MESSAGE_FETCHBOOLEANPAIRS}`)
        
        await instance.initialize(); // Initializes the MSAL instance to avoid BrowserAuthError
        
        const tokenResponse = await instance.acquireTokenSilent({
          ...loginRequest,
          account: activeAccount || undefined
        }) 
        const accessToken = tokenResponse.accessToken // Assigns the access token to a variable
        const idToken = tokenResponse.idToken
        console.log(`${process.env.REACT_APP_MESSAGE_ACCESSTOKEN}`);
        console.log(`${process.env.REACT_APP_MESSAGE_IDTOKEN}`)
        
        const idTokenClaims = tokenResponse.idTokenClaims as any;
        // await collectUserInfo(idTokenClaims, accessToken, idToken);
        
        const firstName = idTokenClaims.given_name || idTokenClaims.name?.split(' ')[0];
        const lastName = idTokenClaims.family_name || idTokenClaims.name?.split(' ').slice(1).join(' ');
        const email = idTokenClaims.email || idTokenClaims.preferred_username;

        if(idTokenClaims.groups){
          console.log("Group IDs are: ", idTokenClaims.groups);
        } else{
          console.log("No groups were found")
        }

        const ipAddress = await getIpAddress();
        console.log("IP ADDRESS IS: ", ipAddress);

        const reader = "ed847544-8bef-48af-b545-f5cd06fd076a";
        const modifier = "6d4ef383-863e-4a3c-a41b-5931036baa4f"
        const role = groupIdToRoleMap[modifier];
        setRoles([role]);
        console.log("Role value: ", roles)


        setUserInfo({ firstName, lastName, email });

        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs`, { // Fetches the boolean pairs from the backend server
          headers: {
            Authorization: `Bearer ${accessToken}`, // Sets the authorization header with the access token
            Authentication: `Bearer ${idToken}`
          },
        })

        const data = await response.json(); // Parses the JSON data and assigned to a variable
        console.log("Boolean pairs fetched successfully")
        setBooleanPairs(data); // Sets the parsed data to the state
      } catch (error) {
        console.error("Error fetching boolean pairs", error);
      }
    };
    if(instance.getActiveAccount()){
      fetchBooleanPairs(); // Calls the function to fetch the boolean pairs
    }
  }, [instance]);

  // useEffect(() => {
  //   if (accounts.length > 0) {
  //       instance.acquireTokenSilent({
  //           ...loginRequest,
  //           account: accounts[0]
  //       }).then((response) => {
  //           callMsGraph(response.accessToken).then(data => {
  //               // console.log("User data from Graph API:", data); 
  //               if (data.value && data.value.length > 0) {
  //                   data.value.forEach((group, index) => {
  //                       // console.log(`Group ${index}:`, group);
  //                       // console.log(`Group ${index} properties:`, Object.keys(group));
  //                   });
  //                   const roles = data.value.map(group => groupIdToRoleMap[group.id] || "Unnamed Group"); 
  //                   setRoles(roles);
  //                   console.log(`Roles retrieved: ${roles}`);
  //               } else {
  //                   console.log("No groups found in the response.");
  //               }
  //           });
  //       }).catch((error) => {
  //           if (error instanceof InteractionRequiredAuthError) {
  //               instance.acquireTokenPopup({
  //                   ...loginRequest,
  //                   account: accounts[0]
  //               }).then((response) => {
  //                   callMsGraph(response.accessToken).then(data => {
  //                       console.log("User data from Graph API:", data); 
  //                       if (data.value && data.value.length > 0) {
  //                           data.value.forEach((group, index) => {
  //                               // console.log(`Group ${index}:`, group);
  //                               // console.log(`Group ${index} properties:`, Object.keys(group));
  //                           });
  //                           const roles = data.value.map(group => groupIdToRoleMap[group.id] || "Unnamed Group"); 
  //                           setRoles(roles);
  //                           console.log(`Roles retrieved: ${roles}`);
  //                       } else {
  //                           console.log("No groups found in the response.");
  //                       }
  //                   });
  //               });
  //           }
  //       });
  //   }
  // }, [accounts, instance]);

//   useEffect(() => {
//     if (accounts.length > 0) {
//         instance.acquireTokenSilent({
//             ...loginRequest,
//             account: accounts[0]
//         }).then((response) => {
//             callMsGraph(response.accessToken).then(data => {
//                 console.log("User data from Graph API:", data); // Log the user data
//                 if (data.value && data.value.length > 0) {
//                     data.value.forEach((group, index) => {
//                         console.log(`Group ${index}:`, group);
//                         console.log(`Group ${index} properties:`, Object.keys(group));
//                     });
//                     const roles = data.value.map(group => group.displayName || "Unnamed Group"); // Extract the group names
//                     setRoles(roles);
//                     console.log(`Roles retrieved: ${roles}`);
//                 } else {
//                     console.log("No groups found in the response.");
//                 }
//             });
//         }).catch((error) => {
//             if (error instanceof InteractionRequiredAuthError) {
//                 instance.acquireTokenPopup({
//                     ...loginRequest,
//                     account: accounts[0]
//                 }).then((response) => {
//                     callMsGraph(response.accessToken).then(data => {
//                         console.log("User data from Graph API:", data); // Log the user data
//                         if (data.value && data.value.length > 0) {
//                             data.value.forEach((group, index) => {
//                                 console.log(`Group ${index}:`, group);
//                                 console.log(`Group ${index} properties:`, Object.keys(group));
//                             });
//                             const roles = data.value.map(group => group.displayName || "Unnamed Group"); // Extract the group names
//                             setRoles(roles);
//                             console.log(`Roles retrieved: ${roles}`);
//                         } else {
//                             console.log("No groups found in the response.");
//                         }
//                     });
//                 });
//             }
//         });
//     }
// }, [accounts, instance])

  const fetchBooleanPairsAgain = async () => {
    try {
      const activeAccount = instance.getActiveAccount();
      if (!activeAccount) {
        throw new Error(`${process.env.REACT_APP_ERROR_MESSAGE_NOACTIVEACCOUNT}`);
      }
      console.log(`${process.env.REACT_APP_MESSAGE_FETCHBOOLEANPAIRS}`);
      
      await instance.initialize();
      
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount || undefined
      });
      
      const accessToken = tokenResponse.accessToken // Assigns the access token to a variable
      const idToken = tokenResponse.idToken
      console.log(`${process.env.REACT_APP_MESSAGE_ACCESSTOKEN}`);
      console.log(`${process.env.REACT_APP_MESSAGE_IDTOKEN}`)

      const idTokenClaims = tokenResponse.idTokenClaims as any;
      const firstName = idTokenClaims.given_name || idTokenClaims.name?.split(' ')[0];
      const lastName = idTokenClaims.family_name || idTokenClaims.name?.split(' ').slice(1).join(' ');
      const email = idTokenClaims.email || idTokenClaims.preferred_username;

      if(idTokenClaims.groups){
        console.log("Group IDs are: ", idTokenClaims.groups);
      } else{
        console.log("No groups were found")
      }

      const reader = "ed847544-8bef-48af-b545-f5cd06fd076a";
      const modifier = "6d4ef383-863e-4a3c-a41b-5931036baa4f"
      const role = groupIdToRoleMap[modifier];
      setRoles([role]);
      console.log("Role value: ", roles)

      setUserInfo({ firstName, lastName, email });

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Authentication: `Bearer ${idToken}`
        },
      });
      const data = await response.json();
      console.log("Boolean pairs fetched successfully");
      setBooleanPairs(data);
    } catch (error) {
      console.error("Error fetching boolean pairs", error);
    }
  };

  const parseKeywords = (description: string) => { // Function to parse the keywords from the job description
    return booleanPairs.filter((pair) => {
      // Creates a regular expression from the boolean name and checks if it is present in the description
      // A regular expression is a sequence of characters that define a search pattern
      const regex = new RegExp(`\\b${pair.BOOLEANNAME.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i'); // Utilizes "//b"(boundary anchor) to ensure that the match is a whole word
      return regex.test(description); // Returns the booleannames that match the description keywords
      }).map(pair => ({
        BOOLEANNAMEVALUEPAIRID: pair.BOOLEANNAMEVALUEPAIRID, // Maps the pairs to the boolean name value pair id
        BOOLEANNAME: pair.BOOLEANNAME, // Maps the pairs to the boolean name
        BOOLEANVALUE: pair.BOOLEANVALUE.split(',').join(', '), // Maps the pairs to the boolean value and splits the values by commas and flattens the multiple arrays into a single one
        isEditable: false // Flag for whether the boolean name/value is editable or not
      }));
  };
  // Function to parse the job title
  const parseJobTitle = (jobTitle: string) => {
    return Object.keys(keytitlesMapping).find((key) => // Returns the key title that matches the job title
      jobTitle.toLowerCase().includes(key.toLowerCase())
    );
  };

  const parseJobCode = (jobTitle: string): string | null => {
    const jobCodeRegex = /^([A-Z]{2}\d{5})/;
    const match = jobTitle.match(jobCodeRegex);
    return match ? match[1] : null;
  };

  const getUniqueBooleanValues = (booleanPairs: { BOOLEANNAME: string; BOOLEANVALUE: string }[]) => {
    const seenValues = new Set<string>(); // To track unique Boolean Values
    return booleanPairs.filter(pair => {
      if (seenValues.has(pair.BOOLEANVALUE)) {
        return false; // Skip if the Boolean Value is already seen
      }
      seenValues.add(pair.BOOLEANVALUE); // Add the Boolean Value to the set
      return true; // Keep the pair
    });
  };

  // Function to handle the form submission
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Parse experience level from the job title
    handleSubmitReset();
    await timeout(200);
    // const code = parseJobCode(jobTitle)
    // setJobCode(code)
    console.log("The job code is: ", jobCode);
    const matchedKeyTitle = parseJobTitle(jobTitle) as keyof typeof keytitlesMapping; // Assigns variable to the matched key title
    if (matchedKeyTitle) {
      const experienceRange = keytitlesMapping[matchedKeyTitle]; // Assigns variable to the experience range
      setExperience({ from: experienceRange.from, to: experienceRange.to }); // Sets the experience range
      setParsedKeyTitle(matchedKeyTitle); // Sets the parsed key title
    } else {
      setExperience({ from: '', to: '' }); // Resets the experience range
      setParsedKeyTitle(''); // Resets the parsed key title
    }
    // Parse technology requirements from the job description
    const parsedKeywords = parseKeywords(description); // Assigns variable to the parsed keywords
    const uniqueKeywords = getUniqueBooleanValues(parsedKeywords);
    setTechnologyRequirements(
      uniqueKeywords.map((keyword, index) => ({ ...keyword, index }))
    );
    // setTechnologyRequirements(parsedKeywords.map((keyword, index) => ({ ...keyword, index }))); // Sets the parsed keywords for the technology requirements
    setIsSubmitted(true); // Sets the form submission status to true(submit has been clicked)
  };

  const handleReorder = (newTechRequirements: TechnologyRequirement[]) => {
    setTechnologyRequirements(newTechRequirements)
    // console.log("New Order of TechRequirements: ", technologyRequirements)
  }

  // Function to add a technology requirement
  const handleAddTechnology = () => {
    setTechnologyRequirements([...technologyRequirements, { BOOLEANNAME: '', BOOLEANVALUE: '', isEditable: true, index: technologyRequirements.length }]);
  }

  // Function to remove a technology requirement
  const handleRemoveTechnology = (index: number) => {
    setTechnologyRequirements(prevState => prevState.filter((_, i) => i !== index));
  }

  // Function to handle the technology change
  const handleTechnologyChange = (index: number, key: string, newValue: string | number) => {
    setTechnologyRequirements(prevState => {
      const updatedRequirements = [...prevState];
      updatedRequirements[index] = {
        ...updatedRequirements[index],
        [key]: newValue,
        isEditable: key === 'BOOLEANNAME' ? true : updatedRequirements[index].isEditable
      };
      return updatedRequirements;
    });
  };

  // const checkLogoutStatus = async () => {
  //   try{
  //     const activeAccount = instance.getActiveAccount();
  //     await instance.initialize();
  //     if (!activeAccount) {
  //       console.error("No active account, please log in.");
  //       navigate('/'); // Redirect to homepage if no active account
  //       return;
  //     }
  //     const tokenResponse = await instance.acquireTokenSilent({
  //       ...loginRequest,
  //       account: activeAccount || undefined
  //     });
  //     const token = tokenResponse.idToken;
  //     const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/logout`, {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json'
  //       },
  //       body: JSON.stringify({ token })
  //     });
  //     if (response.status === 200) {
  //         console.log('User is still logged in');
  //         // Do not navigate to homepage
  //     } else {
  //         console.log('User has logged out');
  //         navigate('/'); // Redirect to homepage only after successful logout
  //     }
  //   } catch (error) {
  //     console.error('Error verifying token', error);
  //   }      
  // }

  // const handleLogout = () => {
  //   const logoutEvent = new Event('logout');
  //   window.dispatchEvent(logoutEvent);
    
  //   instance.logoutPopup().then(() => {
  //     if(userInfo){
  //       console.log(`User logged out: ${userInfo.firstName} ${userInfo.lastName}, Email: ${userInfo.email}`);
  //     } else{
  //       console.log("User logged out")
  //     }
  //     checkLogoutStatus();
  //   }) .catch((error) => {
  //       console.error("Logout Error or Popup closed without logging out", error);
  //   });
  // }

  useEffect(() => {
    const sessionId = sessionStorage.getItem('sid');
    console.log("SessionID on page load: ", sessionId);
    if (!sessionId) {
        console.error('Session ID is missing on page load');
    }
  }, []);

  const handleLogout = async () => {
    const logoutEvent = new Event('logout');
    window.dispatchEvent(logoutEvent);

    const activeAccount = instance.getActiveAccount();
    if (activeAccount) {
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount || undefined
      });
      const accessToken = tokenResponse.accessToken;
      const idToken = tokenResponse.idToken;
      
      const sessionId = sessionStorage.getItem('sid');
      console.log("SessionID is: ", sessionId)
      
      // if (!sessionId) {
      //   console.error('Session ID is missing');
      //   return;
      // }

      // Send a request to the backend to update the logout time
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/userSessionLogout`, {
          method: 'PUT',
          headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${accessToken}`,
              Authentication: `Bearer ${idToken}`
          },
          body: JSON.stringify({
              sessionId: sessionId
          })
      }).then(response => {
          if (response.ok) {
              console.log('Logout time updated successfully');
              sessionStorage.removeItem('sid');
          } else {
              console.error('Failed to update logout time');
          }
      }).catch(error => {
          console.error('Error updating logout time:', error);
      });
  }

    instance.logoutPopup().then(() => {
        const activeAccount = instance.getActiveAccount();
        if (activeAccount) {
            console.log("Logout popup closed without logging out");
            return; 
        }
        // logoutSuccessful = true;
        if (userInfo) {
            console.log(`User logged out: ${userInfo.firstName} ${userInfo.lastName}, Email: ${userInfo.email}`);
        } else {
            console.log("User logged out");
        }
        // navigate('/');
        window.location.href = `${window.location.origin}`; 
    }).catch((error) => {
        console.error("Logout Error or Popup closed without logging out", error);
    });
  };

  // const handleLogout = () => {
  //   const logoutEvent = new Event('logout');
  //   window.dispatchEvent(logoutEvent);

  //   const logoutRequest = {
  //       postLogoutRedirectUri: window.location.origin, // Redirect to the home page after logout
  //   };

  //   instance.logoutRedirect(logoutRequest).then(() => {
  //       console.log("User logged out");
  //       navigate('/'); // Navigate to the home page after logout
  //   }).catch((error) => {
  //       console.error("Logout Error", error);
  //   });
  // };

  const handleReset = () => { // Function to reset the web application
    // Reset all the states
    setJobUrl('');
    setJobTitle('');
    setDescription('');
    setParsedKeyTitle('');
    setTechnologyRequirements([]);
    setIsSubmitted(false);
    setShowHistory(false);
    setSearchVisible(false);
    fetchBooleanPairsAgain();
    getRecentBooleanHistory();
  }
  
  const timeout = (delay: number) => {
    return new Promise(res => setTimeout(res, delay));
  };

  const handleSubmitReset = () => {
    setTechnologyRequirements([])
    setIsSubmitted(false)
  }

  const handleExperienceChange = (key: keyof ExperienceDetails, value: string) => {
    setExperience(prev => ({ ...prev, [key]: value }));
  };

  const getAuthToken = async (): Promise<string> => {
    try {
      console.log("Requesting auth token...");
      const response = await fetch('https://api.ceipal.com/v1/createAuthtoken/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: 'amukry@cloudresourcing.net',
          password: 'W@terl00!@#', // Replace with your actual password
          api_key: '419d85100123479a433feafdbf6856609c64171b8b06b07921',
          format: '0'
        })
      });
      const contentType = response.headers.get('Content-Type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        console.log("Auth token response:", data);
        return data.token;
      } else if (contentType && contentType.includes('application/xml')) {
        const text = await response.text();
        console.log("Auth token response (XML):", text);
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, "application/xml");
        const tokenElement = xmlDoc.getElementsByTagName("access_token")[0];
        const token = tokenElement ? tokenElement.textContent : null;
        if (token) {
          return token;
        } else {
          throw new Error('Failed to extract auth token from XML response');
        }
      } else {
        const text = await response.text();
        console.error("Unexpected response format:", text);
        throw new Error('Failed to generate auth token');
      }
    } catch (error) {
        console.error("Failed to generate auth token:", error);
        throw new Error('Failed to generate auth token');
    }
  };

  const getActiveJobStatusIds = async (): Promise<number[]> => {
    try {
      console.log("Fetching auth token...");
      const authToken = await getAuthToken();
      console.log("Auth token fetched:", authToken);
  
      console.log("Fetching job status list...");
      const response = await fetch(`https://api.ceipal.com/v1/getJobStatusList?bearer%20token=${authToken}`, {
        // mode: 'no-cors',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });
  
      const responseText = await response.text();
      console.log("Response text:", responseText);
  
      if (!response.ok) {
        throw new Error('Failed to fetch job status list');
      }
  
      const data = JSON.parse(responseText);
      console.log("Job status list fetched:", data);
  
      const activeStatuses = data.filter((status: { id: number; name: string }) => status.name === 'Active');
      const activeStatusIds = activeStatuses.map((status: { id: number }) => status.id);
      console.log("Active job status IDs:", activeStatusIds);
  
      return activeStatusIds;
    } catch (error) {
      console.error('Error fetching active job status IDs:', error);
      return [];
    }
  };
  
  const getJobPostingsByStatusIds = async (statusIds: number[]): Promise<any[]> => {
    try {
      // console.log("Fetching auth token...");
      const authToken = await getAuthToken();
      // console.log("Auth token fetched:", authToken);
  
      const jobPostings: any[] = [];
      for (const statusId of statusIds) {
        console.log(`Fetching job postings for status ID ${statusId}...`);
        const response = await fetch(`https://api.ceipal.com/v1/getJobPostingsList?job_status=${statusId}`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          }
        });
  
        if (!response.ok) {
          throw new Error(`Failed to fetch job postings for status ID ${statusId}`);
        }
  
        const data = await response.json();
        console.log(`Job postings for status ID ${statusId} fetched:`, data);
        jobPostings.push(...data);
      }
  
      console.log("All job postings fetched:", jobPostings);
      return jobPostings;
    } catch (error) {
      console.error('Error fetching job postings:', error);
      return [];
    }
  };

  const fetchJobDescription = async (jobTitle: string, setDescription: (description: string) => void) => {
    const activeStatusIds = await getActiveJobStatusIds();
    const jobPostings = await getJobPostingsByStatusIds(activeStatusIds);
  
    for (const job of jobPostings) {
      if (job.title === jobTitle) {
        setDescription(job.description);
        return;
      }
    }
  
    console.error('Job title not found');
  };

  // const fetchJobInfo = async (token: string) => {
  //   const jobId = jobUrl.split('job_id=')[1];
  //   if (jobId) {
  //     console.log("Job ID extracted from URL:", jobId);
  //     const endpointUrl = `https://api.ceipal.com/v1/getJobPostingDetails/?job_id=${jobId}`;
  //     console.log("Endpoint URL:", endpointUrl);
  //     try {
  //       const response = await fetch(endpointUrl, {
  //         headers: {
  //           'Authorization': `Bearer ${token}`
  //         }
  //       });
  //       if (response.ok) {
  //         const data = await response.json();
  //         console.log("Job details fetched successfully:", data);
  //         // const plainTextDescription = htmlToText(data.public_job_desc, {
  //         //   wordwrap: 200 // Set the wordwrap option to 130 characters per line
  //         // });
  //         setJobTitle(data.public_job_title);
  //         // setDescription(plainTextDescription);
  //         setDescription(data.public_job_desc);
  //         setJobCode(data.job_code);
  //         console.log("Job Code: ", jobCode);
  //       } else {
  //         const text = await response.text();
  //         console.error('Failed to fetch job details, response status:', response.status, 'response text:', text);
  //       }
  //     } catch (error) {
  //       console.error('Error fetching job details:', error);
  //     }
  //   } else {
  //     console.error('Invalid job URL:', jobUrl);
  //   }
  // };

  // const handleFindJobInfo = async (): Promise<void> => {
  //   if (!authToken) {
  //     try {
  //       const token = await getAuthToken();
  //       setAuthToken(token);
  //       setJobId(jobUrl.split('job_id=')[1]);
  //       console.log("Auth token generated and set:", token);
  //     } catch (error) {
  //       console.error('Failed to generate auth token:', error);
  //       return;
  //     }
  //   } else {
  //     fetchJobInfo(authToken);
  //   }
  // };

  // useEffect(() => {
  //   if (authToken && jobId) {
  //     fetchJobInfo(authToken);
  //   }
  // }, [authToken, jobId]);

  // const handleRetrieveWeightages = (weightages: any[]) => {
  //   setWeightageStored(weightages);
  // }

  const extractBooleanNames = () => {
    const names = technologyRequirements.map(req => req.BOOLEANNAME);
    setNameStored(names)
  }

  useEffect(() => {
    extractBooleanNames();
  }, [technologyRequirements])

  useEffect(() => {
    const merged = nameStored.map((name, index) => `"${name}", "${weightageStored[index]?.value.toFixed(2)}"`);
    setMergedArray(merged);
  }, [nameStored, weightageStored]);

  const handleRetrievePhrase = (processedString: string) => {
    setBooleanPhrase(processedString);
  }

  const saveBooleanHistory = async () => {
    const confirmUpdate = window.confirm("Are you sure you want to save the boolean history?");
    if (!confirmUpdate) {
      return;
    }
    
    try{
      const activeAccount = instance.getActiveAccount()
      if(!instance.getActiveAccount()){
        throw new Error(`${process.env.REACT_APP_ERROR_MESSAGE_NOACTIVEACCOUNT}`)
      }
                
      await instance.initialize();
                
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount || undefined,
      });
      const accessToken = tokenResponse.accessToken;
      const idToken = tokenResponse.idToken;
      console.log(`${process.env.REACT_APP_MESSAGE_ACCESSTOKEN}`);
      console.log(`${process.env.REACT_APP_MESSAGE_IDTOKEN}`)
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanSearchHistory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
          Authentication: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          jobTitle,
          jobDescription: description,
          booleanPhrase: booleanPhrase,
          technologyRequirements
        })
      });
      if(response.ok){
        const data = await response.json();
        console.log("Boolean history saved successfully: ", data)
        alert('Boolean Phrase Copied to Clipboard and Saved to History Records');
      } else {
        const errorText = await response.text();
        console.error('Failed to save job info:', errorText);
        alert('Boolean Phrase Copied to Clipboard and Failed to Save into History Records');
      }
    } catch(error){
      console.error('Error saving history record:', error);
      alert('Boolean Phrase Copied to Clipboard and Error Saving into History Records');
    }
  }

  const getBooleanHistory = async (jobTitle: string): Promise<HistoryRecord[] | null> => {
    try {
      const activeAccount = instance.getActiveAccount();
      if (!activeAccount) {
        throw new Error(`${process.env.REACT_APP_ERROR_MESSAGE_NOACTIVEACCOUNT}`);
      }
  
      await instance.initialize();
  
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount || undefined
      });
  
      const accessToken = tokenResponse.accessToken;
      const idToken = tokenResponse.idToken;
  
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanSearchHistory?jobTitle=${jobTitle}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Authentication: `Bearer ${idToken}`
        }
      });
  
      if (response.ok) {
        const data = await response.json();
        console.log("Boolean history fetched successfully: ", data);
        if (Array.isArray(data) && data.length > 0) {
          return data; // Return the array of records
        } else {
          console.error("No records found for the given job title");
          return null;
        }
      } else {
        const errorText = await response.text();
        console.error("Failed to fetch Boolean History; ", errorText);
        return null;
      }
    } catch (error) {
      console.error("Error fetching boolean history: ", error);
      return null;
    }
  };

  const getRecentBooleanHistory = async () => {
    try {
      const activeAccount = instance.getActiveAccount();
      if (!activeAccount) {
        throw new Error(`${process.env.REACT_APP_ERROR_MESSAGE_NOACTIVEACCOUNT}`);
      }
  
      await instance.initialize();
  
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount || undefined
      });
  
      const accessToken = tokenResponse.accessToken;
      const idToken = tokenResponse.idToken;
  
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/recentBooleanSearchHistory`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Authentication: `Bearer ${idToken}`
        }
      });
  
      if (response.ok) {
        const data = await response.json();
        if (data.length > 0) {
          console.log("Recent boolean history fetched successfully: ", data);
          // data.forEach((jobInfo, index) => {
          //   console.log(`Record ${index + 1}:`);
          //   console.log("Job Title:", jobInfo.jobTitle);
          //   console.log("Job Description:", jobInfo.jobDescription);
          //   console.log("Boolean Phrase:", jobInfo.booleanPhrase);
          //   console.log("Search Requirements:", jobInfo.technologyRequirements);
          // });
          setRecentHistory(data);
          console.log("Recent History: ", recentHistory)
          // setShowHistory(true);
        } else {
          console.log("No recent boolean history found");
        }
      } else {
        const errorText = await response.text();
        console.error("Failed to fetch recent boolean history: ", errorText);
      }
    } catch (error) {
      console.error("Error fetching recent boolean history: ", error);
    }
  };

  const viewHistory = (indexOrRecord: number | HistoryRecord) => {
    const confirmView = window.confirm("Are you sure you want to view this Boolean History Record?");
    if (!confirmView) {
      return;
    }
  
    handleReset();
  
    let selectedRecord: HistoryRecord;
    if (typeof indexOrRecord === 'number') {
      selectedRecord = recentHistory[indexOrRecord];
    } else {
      selectedRecord = indexOrRecord;
    }
  
    setJobTitle(selectedRecord.jobTitle);
    setDescription(selectedRecord.jobDescription);
    setTechnologyRequirements(selectedRecord.technologyRequirements.map((req, index) => ({
      BOOLEANNAMEVALUEPAIRID: req.BOOLEANNAMEVALUEPAIRID,
      BOOLEANNAME: req.BOOLEANNAME,
      BOOLEANVALUE: req.BOOLEANVALUE,
      isEditable: false,
      index
    })));
    setBooleanPhrase(selectedRecord.booleanPhrase);
    setProcessedString(selectedRecord.booleanPhrase);
    setIsSubmitted(true);
    setShowHistory(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div>
    {/* Navigation bar */}
        {/* <Navigation /> */}
      {/* Home page container */}
      <div className="app-container">
        <div className='app-title'>
          <h1 className='title'>Smart Recruitment</h1>
          <button onClick={handleLogout} className='logout-button'>Logout</button>
        </div>

        {/* Job title and description form */}
        <div>
          <JobForm
            jobTitle={jobTitle}
            description={description}
            setJobTitle={setJobTitle}
            setDescription={setDescription}
            handleSubmit={handleSubmit}
            onReset={handleReset}
            fetchBooleanPairsAgain={fetchBooleanPairsAgain}
            jobUrl={jobUrl}
            setJobUrl={setJobUrl}
            fetchJobDescription={fetchJobDescription}
            records={recentHistory}
            viewHistory={viewHistory}
            getBooleanHistory={getBooleanHistory}
            getRecentBooleanHistory={getRecentBooleanHistory}
            showHistory={showHistory}
            setShowHistory={setShowHistory}
            searchVisible={searchVisible}
            setSearchVisible={setSearchVisible}
          />

          {/* {showHistory && (
            <HistoryRecords 
              records={recentHistory}
              viewHistory={viewHistory}
              getBooleanHistory={getBooleanHistory}
            />
          )} */}
        </div>

        {isSubmitted && (
          <div className="submitted-container">

            {/* Experience component */}
            <ExperienceSection
              experience={experience}
              handleExperienceChange={handleExperienceChange}
            />
            
            {/* Technology requirements component */}
            <TechRequirements
              technologyRequirements={technologyRequirements}
              handleTechnologyChange={handleTechnologyChange}
              handleAddTechnology={handleAddTechnology}
              handleRemoveTechnology={handleRemoveTechnology}
              fetchBooleanPairsAgain={fetchBooleanPairsAgain}
              handleReorder={handleReorder}
              roles={roles}
              // handleRetrieveWeightages={handleRetrieveWeightages}
              experienceFrom={experience.from}
              experienceTo={experience.to}
              // setExperience = {setExperience}
              jobTitle={jobTitle}
              poolValue = {poolValue}
              setPoolValue = {setPoolValue}
              searchByParameter = {searchByParameter}
              setSearchByParameter = {setSearchByParameter}
              toggleParameters = {toggleParameters}
              setToggleParameters = {setToggleParameters}
              toggleJobTitle = {toggleJobTitle}
              setToggleJobTitle = {setToggleJobTitle}
            />
            
            {/* Boolean string component */}
            <BooleanString 
              technologyRequirements={technologyRequirements}
              handleRetrievePhrase={handleRetrievePhrase}
              jobCode={jobCode}
              setJobCode={setJobCode}
              mergedArray={mergedArray}
              saveBooleanHistory={saveBooleanHistory}
              getRecentBooleanHistory={getRecentBooleanHistory}
              processedString={processedString}
              setProcessedString={setProcessedString}
              // mergeNameWeightages={mergeNameWeightages}
            />
            {/* {showHistory && (
              <HistoryRecords 
                records={recentHistory}
                viewHistory={viewHistory}
                getBooleanHistory={getBooleanHistory}
              />
            )} */}
          </div>
        )}
      </div>
    </div>
  )
}

export default App;
