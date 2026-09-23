/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the technology requirements component for recruiters to input the technology requirements after clicking the submit button
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: February 4th, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
//Imported Libraries
import React, {useState, useEffect, ChangeEvent} from "react";
import { FaPlusCircle, FaMinusCircle, FaSave, FaSearch, FaGripVertical, FaCaretDown, FaCaretUp, FaTrash, FaBinoculars } from "react-icons/fa";
import {ToastContainer, toast} from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import {Tooltip} from "react-tooltip"
import './smartrecruitment.css';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfigur.ts";
// import { loginRequest } from "../authConfigur";
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { ThreeDots } from 'react-loader-spinner'
import ViewCVModal from "./ViewCVModal.tsx";

//Interface for the technology requirements
interface TechRequirementsProps {
    technologyRequirements: {BOOLEANNAMEVALUEPAIRID?: number; BOOLEANNAME: string; BOOLEANVALUE: string; weightage?: string; isEditable?: boolean; index: number;}[];
    handleTechnologyChange: (index: number, field: string, value: string | number) => void;
    handleAddTechnology: () => void;
    handleRemoveTechnology: (index: number) => void;
    fetchBooleanPairsAgain: () => void;
    handleReorder: (newTechRequirements: {BOOLEANNAMEVALUEPAIRID?: number; BOOLEANNAME: string; BOOLEANVALUE: string; weightage?: string; isEditable?: boolean; index: number;}[]) => void;
    roles: string[];
    // handleRetrieveWeightages: (weightages: any[]) => void;
    experienceFrom: string;
    experienceTo: string;
    // setExperience: (experienceFrom: string, experienceTo: string) => void;
    jobTitle: string; 
    // weightages: {value: number, isChanged: boolean}[]
    // setWeightages: (weightages: {value: number, isChanged: boolean}[]) => void;
    // calculateInitialWeightages: () => { value: number, isChanged: boolean }[];
    poolValue: number;
    setPoolValue: (poolValue: number) => void;
    searchByParameter: string;
    setSearchByParameter: (searchByParameter: string) => void;
    toggleParameters: boolean;
    setToggleParameters: (toggleParameters: boolean) => void;
    toggleJobTitle: boolean;
    setToggleJobTitle: (toggleJobTitle: boolean) => void;
}

interface ApiResponse {
  results?: any;
  error?: string;
}

const TechRequirements: React.FC<TechRequirementsProps> = ({ //Function to handle the technology requirements(adding, removing, updating or saving)
    technologyRequirements, 
    handleTechnologyChange, 
    handleAddTechnology, 
    handleRemoveTechnology,
    fetchBooleanPairsAgain,
    handleReorder,
    roles,
    // handleRetrieveWeightages,
    experienceFrom,
    experienceTo,
    // setExperience,
    jobTitle,
    poolValue,
    setPoolValue,
    searchByParameter,
    setSearchByParameter,
    toggleParameters,
    setToggleParameters,
    toggleJobTitle,
    setToggleJobTitle
    // weightages,
    // setWeightages,
    // calculateInitialWeightages
}) => {
    const [weightages, setWeightages] = useState<{value: number, isChanged: boolean}[]>([]); // State for the weightages
    const [previousWeightages, setPreviousWeightages] = useState<{value: number, isChanged: boolean}[]>([]);
    const [isAddingRow, setIsAddingRow] = useState<boolean>(false); // State for the adding row status
    const [inputValues, setInputValues] = useState<string[]>([]); // State for the input values
    const [shouldCalculateInitialWeightages, setShouldCalculateInitialWeightages] = useState<boolean>(true);
    const [shouldAdjustWeightages, setShouldAdjustWeightages] = useState<boolean>(false)
    // const [swappingIndex, setSwappingIndex] = useState<number | null>(null);
    const [searchVisible, setSearchVisible] = useState<boolean>(false);
    const [searchInput, setSearchInput] = useState<string>("");
    const [searchResult, setSearchResult] = useState<{BOOLEANNAMEVALUEPAIRID?: number; BOOLEANNAME: string; BOOLEANVALUE: string; weightage?: string; isEditable?: boolean; index: number;} | null>(null);
    const [searchResults, setSearchResults] = useState<any[]>([]); // State for the search results
    const [loading, setLoading] = useState<boolean>(false);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [numCandidates, setNumCandidates] = useState<number>(10);
    const [currentIndex, setCurrentIndex] = useState<number | null>(null);
    const [showRows, setShowRows] = useState<boolean>(true);
    const [showCandidates, setShowCandidates] = useState<boolean>(true);
    const resultsPerPage = 10; // Number of results to display per page
    const [modalIsOpen, setModalIsOpen] = useState(false);
    const [currentFile, setCurrentFile] = useState<string | null>(null);
    // const [currentKeywordCounts, setCurrentKeywordCounts] = useState<{ [key: string]: number } | null>(null);
    const [currentKeywordCounts, setCurrentKeywordCounts] = useState<{
      [key: string]: { 
        count: number; 
        related_keywords: { keyword: string; count: number }[]; // Updated structure
      };
    } | null>(null);
    
    const { instance, accounts } = useMsal();

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

      // useEffect(() => {
      //   handleRetrieveWeightages(weightages);
      // }, [weightages, handleRetrieveWeightages]);

      // useEffect(() => {
      //   const updatedTechRequirements = technologyRequirements.map((tech, index) => ({
      //     ...tech,
      //     weightage: weightages[index] ? weightages[index].value.toString() : "0",
      //   }));
      //   handleReorder(updatedTechRequirements);
      // }, [weightages, technologyRequirements, handleReorder]);

      // useEffect(() => {
      //   if (weightages.length > 0) {
      //     const updatedTechRequirements = technologyRequirements.map((tech, index) => ({
      //       ...tech,
      //       weightage: weightages[index] ? weightages[index].value.toString() : tech.weightage || "0",
      //     }));
      
      //     // Check if the technologyRequirements array has actually changed
      //     const hasChanged = updatedTechRequirements.some((tech, index) => tech.weightage !== technologyRequirements[index].weightage);
      
      //     if (hasChanged) {
      //       handleReorder(updatedTechRequirements);
      //       console.log("Updated technologyRequirements:", updatedTechRequirements);
      //     }
      //   }
      // }, [weightages, technologyRequirements, handleReorder]);

      useEffect(() => {
        if (technologyRequirements.length > 0 && weightages.length === 0) {
          const initialWeightages = technologyRequirements.map((tech) => ({
            value: tech.weightage ? parseFloat(tech.weightage) : 0,
            isChanged: false,
          }));
          setWeightages(initialWeightages);
        }
      }, [technologyRequirements]);
    
    useEffect(() => {
      if (shouldCalculateInitialWeightages) {
        const hasZeroWeightage = weightages.some(weightage => weightage.value === 0);
        if(!hasZeroWeightage){
          calculateInitialWeightages();
        }
      }
    }, [technologyRequirements, shouldCalculateInitialWeightages]);

    useEffect(() => {
      if (shouldAdjustWeightages && currentIndex !== null) {
        adjustWeightages();
      }
    }, [shouldAdjustWeightages, currentIndex]);

    
    const openModal = (
      filename: string,
      keywordCounts: { 
        [key: string]: { 
          count: number; 
          related_keywords: { keyword: string; count: number }[]; 
        }; 
      }
    ) => {
      // Ensure related_keywords is always an array
      const sanitizedKeywordCounts = Object.fromEntries(
        Object.entries(keywordCounts).map(([key, value]) => [
          key,
          {
            ...value,
            related_keywords: value.related_keywords || [], // Default to an empty array if undefined
          },
        ])
      );
    
      setCurrentFile(filename);
      setCurrentKeywordCounts(sanitizedKeywordCounts);
      setModalIsOpen(true);
    };

    const closeModal = () => {
      setModalIsOpen(false);
      setCurrentFile(null);
      setCurrentKeywordCounts(null);
    };

    // const openCVInNewTab = (filename: string) => {
    //   const url = `http://localhost:8002/view-resume/${filename}`;
    //   window.open(url, '_blank');
    // };
    
    const adjustWeightages = async () => {
      // await timeout(2000); // Introduce a delay before adjusting weightages

      console.log("Adjusting weightages...");
      const totalWeightage = 100;
      console.log("Weightages: ", weightages);
      const changedWeightages = weightages.filter(weightage => weightage.isChanged);
      const unchangedWeightages = weightages.filter(weightage => !weightage.isChanged);

      console.log("Changed weightages:", changedWeightages);
      console.log("Unchanged weightages:", unchangedWeightages);

      const remainingWeightage = totalWeightage - changedWeightages.reduce((sum, weightage) => sum + weightage.value, 0);
      console.log("Remaining weightage:", remainingWeightage);

      let newWeightageValue = unchangedWeightages.length > 0 ? parseFloat((remainingWeightage / unchangedWeightages.length).toFixed(2)) : 0;
      console.log("New weightage value for unchanged weightages:", newWeightageValue);

      setShouldCalculateInitialWeightages(false);

      setWeightages(prevWeightages => {
          let newWeightages = prevWeightages.map((weightage, index) => {
              if (!weightage.isChanged) {
                  return { value: Math.max(0, newWeightageValue[index] || newWeightageValue), isChanged: false };
              }
              return { ...weightage, isChanged: true }; // Ensure the isChanged flag remains true for changed weightages
          });


          const totalNewWeightage = newWeightages.reduce((sum, weightage) => sum + weightage.value, 0);
          const totalFlaggedWeightage = newWeightages.filter(weightage => weightage.isChanged).reduce((sum, weightage) => sum + weightage.value, 0);

          const allFlagsSet = newWeightages.every(weightage => weightage.isChanged);
          // if(allFlagsSet){
          //   window.confirm("All fields have been adjusted, from now on only one row's weightage can be adjusted at a time.")
          // }

          if (allFlagsSet) {
              console.log("All flags are set. Starting reallocation for all flags set...");
              console.log("Initial weightages:", newWeightages);
              console.log("Remaining excess:", totalNewWeightage - totalWeightage);

              let remainingExcess = totalNewWeightage - totalWeightage;
              let reallocatedWeightage = remainingExcess / (newWeightages.length - 1);
              let newRemainingExcess = 0;

              newWeightages = newWeightages.map((weightage, index) => {
                  if (index !== currentIndex) {
                      let newValue = weightage.value - reallocatedWeightage;
                      if (newValue < 0) {
                          newRemainingExcess -= newValue; // Add the negative value to new remaining excess
                          newValue = 0;
                      }
                      console.log(`Adjusting weightage at index ${index}: newValue = ${newValue.toFixed(2)}`);
                      return { ...weightage, value: parseFloat(newValue.toFixed(2)) };
                  }
                  return weightage;
              });

              console.log("New weightages after reallocation for all flags set:", newWeightages);
              console.log("New remaining excess:", newRemainingExcess);

              setInputValues(newWeightages.map(weightage => weightage.value.toString()));
              newWeightages.forEach((weightage, idx) => handleTechnologyChange(idx, 'weightage', weightage.value));

              return newWeightages;
          }
          if (totalFlaggedWeightage > totalWeightage) {
              const proceed = window.confirm("The total weightage exceeds 100. Do you want to proceed with adjusting the weightages?");
              if (proceed) {
                  const excessWeightage = totalNewWeightage - totalWeightage;
                  let remainingExcess = excessWeightage;

                  const reallocateWeightage = (weightages, remainingExcess, currentIndex, bypassFlag = false) => {
                      console.log("Starting reallocation...");
                      console.log("Initial weightages:", weightages);
                      console.log("Remaining excess:", remainingExcess);
                      console.log("Current index:", currentIndex);

                      let reallocatedWeightage = remainingExcess / (weightages.length - 1);
                      let newRemainingExcess = 0;

                      const newWeightages = weightages.map((weightage, idx) => {
                          if (idx !== currentIndex || bypassFlag) {
                              let newValue = weightage.value - reallocatedWeightage;
                              if (newValue < 0) {
                                  newRemainingExcess -= newValue; // Add the negative value to new remaining excess
                                  newValue = 0;
                              }
                              console.log(`Adjusting weightage at index ${idx}: newValue = ${newValue.toFixed(2)}`);
                              return { ...weightage, value: parseFloat(newValue.toFixed(2)) };
                          }
                          return weightage;
                      });

                      console.log("New weightages after reallocation:", newWeightages);
                      console.log("New remaining excess:", newRemainingExcess);

                      if (newRemainingExcess > 0 && newRemainingExcess !== remainingExcess) {
                          const nonZeroWeightages = newWeightages.filter((weightage, idx) => (idx !== currentIndex || bypassFlag) && weightage.value > 0);
                          if (nonZeroWeightages.length > 0) {
                              const newReallocatedWeightage = newRemainingExcess / nonZeroWeightages.length;
                              newRemainingExcess = 0;

                              const finalWeightages = newWeightages.map((weightage, idx) => {
                                  if ((idx !== currentIndex || bypassFlag) && weightage.value > 0) {
                                      let newValue = weightage.value - newReallocatedWeightage;
                                      if (newValue < 0) {
                                          newRemainingExcess += newValue; // Add the negative value to new remaining excess
                                          newValue = 0;
                                      }
                                      console.log(`Final adjusting weightage at index ${idx}: newValue = ${newValue.toFixed(2)}`);
                                      return { ...weightage, value: parseFloat(newValue.toFixed(2)) };
                                  }
                                  return weightage;
                              });

                              console.log("Final weightages after reallocation:", finalWeightages);
                              console.log("Final remaining excess:", newRemainingExcess);

                              if (newRemainingExcess > 0 && newRemainingExcess !== remainingExcess) {
                                  return reallocateWeightage(finalWeightages, newRemainingExcess, currentIndex, bypassFlag);
                              }

                              return finalWeightages;
                          }
                      }

                      return newWeightages;
                  };

                newWeightages = reallocateWeightage(newWeightages, remainingExcess, currentIndex);
            } else{
                newWeightages = [...previousWeightages];
                setWeightages(newWeightages);
                setInputValues(newWeightages.map(weightage => weightage.value.toString()));
                return newWeightages;
            }
          }

          console.log("New weightages:", newWeightages);
          console.log("Weightages after setting in adjustWeightages:", newWeightages);

          setInputValues(newWeightages.map(weightage => weightage.value.toString()));
          newWeightages.forEach((weightage, idx) => handleTechnologyChange(idx, 'weightage', weightage.value));

          return newWeightages;
      });
      setShouldAdjustWeightages(false); // Reset the flag
    };

    const toggleRows = () => {
      setShowRows(!showRows);
    };

    const toggleCandidates = () => {
      setShowCandidates(!showCandidates);
    }
      
      const calculateInitialWeightages = () => {
        // const totalWeightage = 100;
        // let initialWeightages = technologyRequirements.map((tech, index) => {
        //   const existingWeightage = weightages[index];
        //   return {
        //     value: tech.weightage ? parseFloat(tech.weightage) : parseFloat((totalWeightage / technologyRequirements.length).toFixed(2)),
        //     isChanged: existingWeightage ? existingWeightage.isChanged : false,
        //   };
        // });
    
        // // Preserve weightages that have been set to 0 or changed
        // initialWeightages = initialWeightages.map((weightage, index) => {
        //   if (weightages[index] && weightages[index].isChanged) {
        //     return weightages[index];
        //   }
        //   return weightage;
        // });
    
        // setWeightages(initialWeightages);
        // setInputValues(initialWeightages.map(weightage => weightage.value.toString()));
        const totalWeightage = 100;
        const flaggedWeightages = weightages.filter(weightage => weightage.isChanged);
        const unflaggedWeightages = weightages.filter(weightage => !weightage.isChanged);
      
        if (flaggedWeightages.length > 0) {
          // Calculate the sum of flagged weightages
          const flaggedWeightageSum = flaggedWeightages.reduce((sum, weightage) => sum + weightage.value, 0);
          // Calculate the remaining weightage to be distributed among unflagged weightages
          const remainingWeightage = totalWeightage - flaggedWeightageSum;
          // Calculate the new weightage value for unflagged weightages
          const newWeightageValue = remainingWeightage / (technologyRequirements.length - flaggedWeightages.length);
      
          let initialWeightages = technologyRequirements.map((tech, index) => {
            const existingWeightage = weightages[index];
            if (existingWeightage && existingWeightage.isChanged) {
              return existingWeightage;
            }
            return {
              value: parseFloat(newWeightageValue.toFixed(2)),
              isChanged: false,
            };
          });
      
          setWeightages(initialWeightages);
          setInputValues(initialWeightages.map(weightage => weightage.value.toString()));
        } else {
          // Original logic for calculating initial weightages when no weightages are flagged
          let initialWeightages = technologyRequirements.map((tech, index) => {
            const existingWeightage = weightages[index];
            return {
              value: tech.weightage ? parseFloat(tech.weightage) : parseFloat((totalWeightage / technologyRequirements.length).toFixed(2)),
              isChanged: existingWeightage ? existingWeightage.isChanged : false,
            };
          });
      
          // Preserve weightages that have been set to 0 or changed
          initialWeightages = initialWeightages.map((weightage, index) => {
            if (weightages[index] && weightages[index].isChanged) {
              return weightages[index];
            }
            return weightage;
          });
      
          setWeightages(initialWeightages);
          setInputValues(initialWeightages.map(weightage => weightage.value.toString()));
        }
      };
    
      const adjustWeightagesOnAdd = () => {
        // const hasChangedWeightage = weightages.some(weightage => weightage.isChanged);
        // if(hasChangedWeightage){
        //   setShouldAdjustWeightages(true);
        //   console.log("Weightages have been adjusted: ", hasChangedWeightage, weightages)
        // } else{
          // setShouldAdjustWeightages(false)
          const totalWeightage = 100;
          let initialWeightages = technologyRequirements.map((tech) =>
            tech.weightage || (totalWeightage / technologyRequirements.length).toFixed(2)
          );
      
          const weightageSum = initialWeightages.reduce((sum, val) => sum + parseFloat(val), 0);
          if (weightageSum !== totalWeightage) {
            const lastIdx = initialWeightages.length - 1;
            initialWeightages[lastIdx] = (parseFloat(initialWeightages[lastIdx]) + totalWeightage - weightageSum).toFixed(2);
          }
          setWeightages(initialWeightages.map(weightage => ({ value: parseFloat(weightage), isChanged: false })));
          setInputValues(initialWeightages);
          setIsAddingRow(false);
        // }
        // setShouldAdjustWeightages(true);
      };
    
    const adjustWeightagesOnRemove = () => {  
      // const hasChangedWeightage = weightages.some(weightage => weightage.isChanged);
      // if(hasChangedWeightage){
      //   setShouldAdjustWeightages(true);
      //   console.log("Weightages have been adjusted: ", hasChangedWeightage, weightages)
      // } else{
        // setShouldAdjustWeightages(false)
        const totalWeightage = 100;
        let initialWeightages = technologyRequirements.map((tech) =>
          tech.weightage || (totalWeightage / technologyRequirements.length).toFixed(2)
        );
        setWeightages(initialWeightages.map(weightage => ({ value: parseFloat(weightage), isChanged: false })));
        setInputValues(initialWeightages);
    };

    const handleInputChange = async (index: number, value: string) => { // Function to handle the input change
      console.log(`Received index: ${index} (type: ${typeof index})`);
      console.log(`Received value: ${value} (type: ${typeof value})`);
  
      if (index < 0 || index >= weightages.length) {
        console.error(`Invalid index: ${index}`);
        return;
      }
      
      setCurrentIndex(index);
      setShouldCalculateInitialWeightages(false);

      const newInputValues = [...inputValues];
      newInputValues[index] = value;
      setInputValues(newInputValues);

      setPreviousWeightages(weightages)
  
      setWeightages(prevWeightages => {
        let newWeightages = [...prevWeightages];
        const newValue = parseFloat(value) || 0;

        if (newValue < 0) {
            window.confirm("Negative numbers are not allowed. The weightage has been reset to its previous state.");
            newWeightages = [...previousWeightages];
            setWeightages(newWeightages);
            setInputValues(newWeightages.map(weightage => weightage.value.toString()));
            return newWeightages;
        }

        if (newValue > 100) {
          window.confirm("Numbers greater than 100 are not allowed. The weightage has been reset to 100.");
          newWeightages[index] = { value: 100, isChanged: true };
          setWeightages(newWeightages);
          setInputValues(newWeightages.map(weightage => weightage.value.toString()));
          handleTechnologyChange(index, 'weightage', 100);
          return newWeightages;
        }

        newWeightages[index] = { value: newValue, isChanged: true };

        // const trueFlagsCount = newWeightages.filter(weightage => weightage.isChanged).length;
        // if (trueFlagsCount === newWeightages.length) {
        //   newWeightages = newWeightages.map((weightage, idx) => {
        //       if (idx === index) {
        //           return { ...weightage, isChanged: true };
        //       }
        //       return { ...weightage, isChanged: false };
        //   });
        // }

        console.log("Updated weightages:", newWeightages);
        console.log("Weightages after setting in handleInputChange:", weightages); 

        handleTechnologyChange(index, 'weightage', newWeightages[index].value);
        console.log(`Passing index to handleWeightageInputChange: ${index} (type: ${typeof index})`);

        const updatedTechRequirements = technologyRequirements.map((tech, idx) => {
          if (idx === index) {
            return { ...tech, weightage: newWeightages[idx].value.toString() };
          }
          return tech;
        });
        handleReorder(updatedTechRequirements);

        return newWeightages;
      });

      setShouldAdjustWeightages(true);
    };

    const handleUpdate = async (index: number) => { // Function to handle the update process
        const tech = technologyRequirements[index];
        console.log("Updating technology requirement:", tech);
        
        // Warns the user before updating/saving the technology requirement
        const confirmUpdate = window.confirm("Are you sure you want to update this search requirement?");
        if (!confirmUpdate) {
          return;
        }

        if (!tech.BOOLEANNAME.trim() || !tech.BOOLEANVALUE.trim()) {
          alert("Boolean Name and Boolean Value fields cannot be empty.");
          console.error("Empty Boolean Name and Boolean Value Fields");
          toast.error("Empty Boolean Name and Boolean Value Fields");
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
          
          const existingResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs/`, {
            headers:{
              Authorization: `Bearer ${accessToken}`,
              Authentication: `Bearer ${idToken}`
            }
          }); // Fetches the existing response from the backend server
          const existingData = await existingResponse.json(); // Parses the JSON data and assigned to a variable
          const isDuplicate = existingData.some((entry: {BOOLEANNAME: string; BOOLEANVALUE: string; BOOLEANNAMEVALUEPAIRID?: number}) =>
            entry.BOOLEANNAME.toLowerCase() === tech.BOOLEANNAME.toLowerCase() &&
            entry.BOOLEANVALUE.toLowerCase() === tech.BOOLEANVALUE.toLowerCase()
          ); // Checks if a duplicate technology requirement is being saved into the database

          if(isDuplicate){ // Checks if a duplicate technology requirement is being saved into the database
            console.error(`${process.env.REACT_APP_ERROR_MESSAGE_DUPLICATE_RECORD}`, tech);
            toast.error(`${process.env.REACT_APP_ERROR_MESSAGE_DUPLICATE_RECORD}`);
            return;
          }

          if(tech.BOOLEANNAMEVALUEPAIRID){ // Checks if the technology requirement exists
            // Updates the technology requirement
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs/${tech.BOOLEANNAMEVALUEPAIRID}`, {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`, // Access token is used for authorization
                Authentication: `Bearer ${idToken}`
              },
              body: JSON.stringify({
                BOOLEANNAME: tech.BOOLEANNAME,
                BOOLEANVALUE: tech.BOOLEANVALUE
              })
            });
            if (response.ok) {
              const updatedTech = await response.json();
              alert("Record Updated Successfully");
              console.log(`${process.env.REACT_APP_ERROR_MESSAGE_RECORD_UPDATESUCCESSFUL}`, updatedTech);
              toast.success(`${process.env.REACT_APP_ERROR_MESSAGE_RECORD_UPDATESUCCESSFUL}`); // Notifies the user that the technology requirement has been updated using the toastify library
              fetchBooleanPairsAgain(); // Fetches the boolean pairs again
            } else {
              alert("Record Failed To Update")
              console.error(`${process.env.REACT_APP_ERROR_MESSAGE_RECORD_UPDATEFAILURE}`);
              toast.error(`${process.env.REACT_APP_ERROR_MESSAGE_RECORD_UPDATEFAILURE}`);
            }
          } else { // Adds a new technology requirement to the database
              const hightestId = existingData.reduce((maxId: number, entry: {BOOLEANNAMEVALUEPAIRID?: number}) => Math.max(maxId, entry.BOOLEANNAMEVALUEPAIRID ?? 0), 0); // Calculates the id of the new technology requirement
              const newId = hightestId + 1; // Assigns the new id to the new technology requirement 

              // Adds the new technology requirement
              const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs/`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`, // Access token is used for authorization
                    Authentication: `Bearer ${idToken}`
                  },
                  body: JSON.stringify({
                    BOOLEANNAMEVALUEPAIRID: newId,
                    BOOLEANNAME: tech.BOOLEANNAME,
                    BOOLEANVALUE: tech.BOOLEANVALUE
                  })
                });
                if(response.ok){
                  const newTech = await response.json();
                  alert("Record Added Successfully")
                  console.log("Added successfully: ", newTech);
                  toast.success("Added successfully");
                  fetchBooleanPairsAgain(); // Fetches the boolean pairs again
                } else {
                  alert("Record Failed to Add")  
                  console.error("Failed to add");
                  toast.error("Failed to add");
                }
            }
        } catch (error) {
          console.error("Error updating technology requirement: ", error);
          toast.error("Error updating technology requirement");
        }
    }

    const handleDelete = async (id: number) => {
      const confirmDelete = window.confirm("Are you sure you want to delete this record?")
      if (!confirmDelete){
        return;
      }

      try{
        const activeAccount = instance.getActiveAccount();  
        if(!activeAccount){
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

        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs/${id}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            Authentication: `Bearer ${idToken}`
          },
        });

        if(response.ok) {
          alert("Record Deleted Successfully")
          console.log(`Deleted successfully: ${technologyRequirements.find(tech => tech.BOOLEANNAMEVALUEPAIRID === id)?.BOOLEANNAME} - ${technologyRequirements.find(tech => tech.BOOLEANNAMEVALUEPAIRID === id)?.BOOLEANVALUE}` );
          toast.success("Deleted successfully");
          fetchBooleanPairsAgain();
        } else{
          alert("Failed to Delete Record");
          console.error("Failed to Delete Record");
          toast.error("Failed to Delete Record");
        }
      } catch (error) {
        console.error("Error deleting technology requirement: ", error);
        toast.error("Error deleting technology requirement");        
      }
    };

    const timeout = (delay: number) => {
      return new Promise(res => setTimeout(res, delay));
    };
    const thehandleAddTechnology = async () => { // Function to handle the adding of a technology requirement
      // const hasChangedWeightage = weightages.some(weightage => weightage.isChanged);
      // if (hasChangedWeightage){
      //   console.log("Flag is up", hasChangedWeightage)
      //   handleAddTechnology();
      //   setIsAddingRow(true);
      //   adjustWeightagesOnAdd()
      //   await timeout(1000);
      //   setShouldCalculateInitialWeightages(true);
      //   console.log("Flag is up", hasChangedWeightage)
      //   // setShouldCalculateInitialWeightages(false);
      // }else{
      //   handleAddTechnology();
      //   setIsAddingRow(true);
      //   adjustWeightagesOnAdd();
      //   calculateInitialWeightages();
      //   setShouldCalculateInitialWeightages(true);
      // }
      const hasChangedWeightage = weightages.some(weightage => weightage.isChanged);
      handleAddTechnology();
      setIsAddingRow(true);
      adjustWeightagesOnAdd();
      console.log("technologyRequirements after adding a technology:", technologyRequirements);
    
      if (hasChangedWeightage) {
        console.log("Flag is up", hasChangedWeightage);
        // await timeout(1000);
        setShouldCalculateInitialWeightages(true);
        calculateInitialWeightages();
        console.log("Flag is up", hasChangedWeightage);
      } else {
        calculateInitialWeightages();
        setShouldCalculateInitialWeightages(true);
      }
    };

    const thehandleRemoveTechnology = (index: number) => {
      handleRemoveTechnology(index);
      adjustWeightagesOnRemove();
      calculateInitialWeightages();
      setShouldCalculateInitialWeightages(true);
  };

    const formatTooltipContent = (content: string) => { // Function to format the tooltip content
      const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/g;
      return content.replace(regex, "<br>");
    };

    const handleDragEnd = (result) => {
      if (!result.destination) return; // If the item is dropped outside the list, just return

      const newTechRequirements = Array.from(technologyRequirements); // Copy the array and assign it to a temporary one
      const [movedItem] = newTechRequirements.splice(result.source.index, 1); // Remove the item from the source index
      newTechRequirements.splice(result.destination.index, 0, movedItem); // Insert the item at the destination index
  
      // Update the index of each item to ensure they are consecutive
      newTechRequirements.forEach((tech, idx) => tech.index = idx);
  
      const newWeightages = Array.from(weightages); // Copy the weightages array
      const [movedWeightage] = newWeightages.splice(result.source.index, 1); // Remove the weightage from the source index
      newWeightages.splice(result.destination.index, 0, movedWeightage); // Insert the weightage at the destination index
  
      handleReorder(newTechRequirements);
      setWeightages(newWeightages);
    };

    const handleSearch = async () => {
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

        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/booleanPairs`, {
          headers: {
              Authorization: `Bearer ${accessToken}`,
              Authentication: `Bearer ${idToken}`,
          },
        });

        const data = await response.json();
        const result = data.find((entry: { BOOLEANNAME: string }) =>
            entry.BOOLEANNAME.toLowerCase() === searchInput.toLowerCase()
        );

        if (result) {
            setSearchResult(result);
        } else {
            toast.error("Boolean name not found");
        }
      } catch (error) {
        console.error("Error searching boolean name:", error);
        toast.error("Error searching boolean name");
      }
    }

    const handleAddSearchedTechnology = () => {
      if(searchResult){
        const newTechRequirements = [...technologyRequirements,
          {
            BOOLEANNAMEVALUEPAIRID: searchResult.BOOLEANNAMEVALUEPAIRID,
            BOOLEANNAME: searchResult.BOOLEANNAME,
            BOOLEANVALUE: searchResult.BOOLEANVALUE,
            isEditable: false,
            index: technologyRequirements.length
          }
        ];
        handleReorder(newTechRequirements);
        setSearchVisible(false);
        setSearchInput("");
        setSearchResult(null);
      }
    }

    const handleCancelSearch = () => {
      setSearchVisible(false);
      setSearchInput("");
      setSearchResult(null)
    }

    const parseJobTitle = (jobTitle: string): string => {
      const parts = jobTitle.split(" - ");
      // // Filter out parts that are purely numeric
      // const filteredParts = parts.filter(part => isNaN(Number(part.trim())));
      // // Join the remaining parts back together
      // return filteredParts.slice(1).join(" - ").trim();
      const filteredParts = parts.filter(
        part => !/^\d+$/.test(part.trim()) && !/^(RQ|ML|[A-Z]{2,})\d*/.test(part.trim())
      );
    
      // Join the remaining parts back together
      return filteredParts.join(" - ").trim();
    };

    const sendWeightages = async () => {
      if((experienceFrom === "") && (experienceTo === "")){
        alert("Both Experience fields are empty. Please fill in at least one of them");
        console.error("Both Experience fields are empty.");
        return;
      }
      setLoading(true);
      
      const booleanQueryArray = technologyRequirements.map((req, index) => `"${req.BOOLEANNAME}", "${weightages[index].value.toFixed(2)}"`);
      
      const booleanNameValue = technologyRequirements.map(req => ({
        BOOLEANNAME: req.BOOLEANNAME,
        BOOLEANVALUE: req.BOOLEANVALUE,
      }));

      const booleanQueryString = booleanQueryArray.join(' AND ');
      const experienceFromValue = experienceFrom === "" ? "0" : experienceFrom;
      const experienceToValue = experienceTo === "" ? "0" : experienceTo;

      const parsed_jobTitle = parseJobTitle(jobTitle)

      console.log(`Parsed job title: ${parsed_jobTitle} `)

      let jobQuery = "";
      if (searchByParameter === "Boolean Name") {
        // Boolean Names are passed over with the job title
        jobQuery = `${parsed_jobTitle} with skills in ${technologyRequirements.map(tech => tech.BOOLEANNAME).join(", ")}`;
      } else if (searchByParameter === "Boolean Value") {
        // Boolean Values are passed over with the job title
        jobQuery = `${parsed_jobTitle} with skills in ${technologyRequirements
          .map(tech => tech.BOOLEANVALUE
            .replace(/ OR /g, ", ") // Replace "OR" with ", " for proper formatting within groups
            .replace(/"/g, "") // Remove all double quotes
            .trim() // Remove leading and trailing spaces
          )
          .join(", ")}`;
      }

      // console.log(booleanQueryString);
      try {
        const response = await fetch(`${process.env.REACT_APP_PYTHON_ROUTE}/search-resumes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              query: booleanQueryString,
              booleanNameValue,
              n_results: numCandidates,
              poolValue,
              toggleJobTitle,
              experienceFromValue,
              experienceToValue,
              jobQuery
            })
        });
        const data: ApiResponse = await response.json();
        if (data.results) {
            setSearchResults(data.results);
        } else if (data.error) {
            console.error("Error adding numbers: ", data.error);
            setSearchResults([]);
        }
      } catch (error) {
          console.error("Error fetching data: ", error);
          setSearchResults([]);
      } finally{
        setLoading(false);
      }
    };

    const handlePageChange = (newPage: number) => {
      setCurrentPage(newPage);
    };
    const indexOfLastResult = currentPage * resultsPerPage;
    const indexOfFirstResult = indexOfLastResult - resultsPerPage;
    const currentResults = searchResults.slice(indexOfFirstResult, indexOfLastResult);


    return (
      <div className="tech-requirements-container">
        <div className="tech-requirements-heading">
          <label className="tech-requirements-title">Search Requirements</label>
          <div className="toggle-icon" onClick={toggleRows}>
            {showRows ? <FaCaretDown title="Hide Items" /> : <FaCaretUp title="Show Items"/>}
          </div>
        </div>
        {showRows && (  
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="tech-requirements-list">
              {(provided) => (
                <div
                  className="tech-requirements-list"
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                >
                  {technologyRequirements.map((tech, index) => (
                    <Draggable key={tech.BOOLEANNAMEVALUEPAIRID || `tech-${index}`} draggableId={tech.BOOLEANNAMEVALUEPAIRID ? tech.BOOLEANNAMEVALUEPAIRID.toString() : `tech-${index}`} index={index}>
                      {(provided, snapshot) => ( // provided contains properties to apply to a draggable element, snap shot contains the state of the draggable element
                        <div
                          ref={provided.innerRef} // Reference to the draggable element
                          {...provided.draggableProps} // Dragging properties
                          // {...provided.dragHandleProps} // Dragging handle properties
                          className={`tech-requirements-item ${snapshot.isDragging ? 'dragging' : ''}`} // Class name for the draggable element
                        >
                        <div className="left-side-buttons">
                          <div {...provided.dragHandleProps} className="drag-handle">
                            <FaGripVertical/>
                          </div>
                          <FaMinusCircle onClick={() => thehandleRemoveTechnology(index)} className="left-button" title="Remove Technology" />
                        </div>
                            
                          {tech.isEditable ? (
                            <input
                              type="text"
                              value={tech.BOOLEANNAME}
                              onChange={(e: ChangeEvent<HTMLInputElement>) => handleTechnologyChange(index, "BOOLEANNAME", e.target.value)}
                              placeholder="Boolean Name"
                              className="tech-requirements-input"
                            />
                          ) : (
                            <span className="tech-requirements-span">
                              {tech.BOOLEANNAME}
                            </span>
                          )}
                          <input
                            type="text"
                            value={tech.BOOLEANVALUE}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => handleTechnologyChange(index, "BOOLEANVALUE", e.target.value)}
                            placeholder="Boolean Value"
                            className="tech-requirements-value"
                            data-tooltip-id={`tooltip-${index}`}
                            data-tooltip-content={formatTooltipContent(tech.BOOLEANVALUE)}
                          />
                          <Tooltip id={`tooltip-${index}`} place="top" variant="dark" />
                          <input
                            type="number"
                            value={weightages[index] ? weightages[index].value : 0}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => handleInputChange(index, e.target.value)}
                            placeholder="Weightage"
                            className={`tech-requirements-weightage ${weightages[index]?.isChanged ? 'changed': ''}`}
                          />
                          <div className="tech-requirements-buttons">
                            {roles.includes("Boolean_Modifier") && (
                              <>
                                <FaSave onClick={() => handleUpdate(index)} className="icon-button" title="Save or Overwrite to Database" />
                                <FaTrash onClick={() => tech.BOOLEANNAMEVALUEPAIRID !== undefined && handleDelete(tech.BOOLEANNAMEVALUEPAIRID)} className="delete-button" title="Delete from Database" />
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder as React.ReactNode}
                </div>
              )}
            </Droppable>
          </DragDropContext>
          )}
          <div className="tech-requirements-add">
            <FaPlusCircle onClick={thehandleAddTechnology} className="icon-button" title="Add Technology"/>
            <FaSearch onClick={() => setSearchVisible(true)} className="icon-button" title="Search Technology" />
          </div>
          {searchVisible && (
            <div className="search-container">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search Boolean Name"
                className="search-input"
              />
                <button onClick={handleSearch} className="search-button">Search</button>
                {searchResult && (
                  <>
                  <div className="search-result">
                      {/* <p>Boolean Name: {searchResult.BOOLEANNAME}</p> */}
                    <input
                      type="text"
                      value={searchResult.BOOLEANVALUE}
                      readOnly
                      className="b-value"
                      data-tooltip-id="search-result-tooltip"
                      data-tooltip-content={searchResult.BOOLEANVALUE}
                    />
                    <Tooltip id="search-result-tooltip" place="top" variant="dark" className="custom-tooltip" />
                  </div>
                    <div className="addcancel-buttons">
                      <button onClick={handleAddSearchedTechnology} className="add-button">Add</button>
                      <button onClick={handleCancelSearch} className="cancel-button">Cancel</button>
                    </div>
                  </>
                )}
            </div>
          )}
          {process.env.REACT_APP_SHOW_CANDIDATES_SECTION === 'true' && (
            <div className="tech-requirements-search">
              <div className="tech-requirements-header">
                <h3 className="candidate=title">Best Suited Candidates</h3>
                <div className="toggle-icon" onClick={toggleCandidates}>
                  {showCandidates ? <FaCaretDown title="Hide Items" /> : <FaCaretUp title="Show Items"/>}
                </div>
              </div>
              {showCandidates && (
                <div className="tech-requirements-search-further">
                  <div className="tech-requirements-retrieve"> 
                    <div className="num-candidates-input">
                      <label htmlFor="num-candidates">Top:</label>
                      <input
                        type="number"
                        id="num-candidates"
                        value={numCandidates}
                        onChange={(e) => setNumCandidates(parseInt(e.target.value))}
                        min="1"
                      />
                    </div> 
                    <button onClick={sendWeightages} className="weightage-button"> Find Candidates </button>
                  </div>
                  {/* New Section for Pool Value and Dropdown */}
                  <div className="additional-options">
                    <div className="toggle-icon-search" onClick={() => setToggleParameters(!toggleParameters)}>
                      {toggleParameters ? <FaMinusCircle title="Hide Options" /> : <FaPlusCircle title="Show Options" />}
                    </div>
                    {toggleParameters && (
                      <div className="additional-options-content">
                        {/* Pool Value Input */}
                        <div className="pool-value-input">
                          <label htmlFor="pool-value" className="pool-value-label">Pool Value:</label>
                          <input
                            type="number"
                            id="pool-value"
                            value={poolValue}
                            onChange={(e) => {
                              const value = e.target.value;
                              if (value === "") {
                                setPoolValue(200); // Default to 500 if the input is cleared
                              } else {
                                setPoolValue(parseInt(value)); // Temporarily set the value without clamping
                              }
                            }}
                            onBlur={(e) => {
                              // Clamp the value when the input loses focus
                              const value = parseInt(e.target.value);
                              if (!isNaN(value)) {
                                setPoolValue(Math.min(Math.max(value, 200), 1000));
                              } else {
                                setPoolValue(200); // Default to 500 if the input is invalid
                              }
                            }}
                            min="200"
                            max="1000"
                          />
                        </div>

                        {/* Dropdown for Boolean Name/Value */}
                        <div className="search-by-parameter">
                          <label htmlFor="search-by" className="search-by-label">Search By:</label>
                          <select
                            id="search-by"
                            value={searchByParameter}
                            onChange={(e) => setSearchByParameter(e.target.value)}
                          >
                            <option value="Boolean Name">Boolean Name</option>
                            <option value="Boolean Value">Boolean Value</option>
                          </select>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px", // Space between the label and the toggle
                            marginBottom: "17px"
                          }}
                        >
                          {/* Label for the toggle */}
                          <label
                            htmlFor="toggle-job-title"
                            style={{
                              fontSize: "16px",
                              fontWeight: "bold",
                              color: "white",
                            }}
                          >
                            Recent Job Title:
                          </label>

                          {/* Toggle Circle */}
                          <div
                            onClick={() => setToggleJobTitle(!toggleJobTitle)} // Toggle the state on click
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              width: "30px",
                              height: "30px",
                              // borderRadius: "50%", // Makes it a circle
                              border: "2px solid white",
                              cursor: "pointer",
                              userSelect: "none",
                            }}
                          >
                            {toggleJobTitle && (
                              <span
                                style={{
                                  fontSize: "20px",
                                  fontWeight: "bold",
                                  color: "white",
                                }}
                              >
                                ✓
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
          {showCandidates && (
            <>
              {loading ? (
                <div>
                  <div className="loading-spinner">
                    <ThreeDots color="white" height={60} width={60} />
                  </div>
                </div>
              ) : (
                  <div className="search-results">
                    {searchResults.length > 0 ? (
                      <div>
                        <ul>
                          {currentResults.map((output, index) => (
                            <div key={index}>
                              <div className="candidates">
                                <li className="search-result-item">
                                  {/* <p className="search-result-detail">Rank: {output.rank}</p> */}
                                  <div className="candidate-heading">
                                    <div className="candidate-info">
                                      <div className="candidate-info-heading">
                                        <h3 className="rank-heading">Rank {output.rank}:</h3>
                                        <h3 className="candidate-name">{output.candidate_name}</h3>
                                      </div>
                                      <FaBinoculars onClick={() => openModal(output.filename, output.keyword_counts)} className="view-resume-button" title="Preview Resume/CV"/>
                                    </div>
                                    <h4 className="relevance-score">Relevance: {output.relevance_score}%</h4>
                                  </div>
                                  <div className="candidate-details-container1">
                                    <div className="candidate-details-row">
                                      <div className="candidate-details-cell">Job Title: <span className="job-title">{output.job_title}</span></div>
                                      <div className="candidate-details-cell">Email: <span className="contact-email">{output.contact_email}</span></div>
                                      <div className="candidate-details-cell">Phone: <span className="contact-phone">{output.contact_phone}</span></div>
                                    </div>
                                  </div>
                                  <div className="candidate-details-container2">
                                    <div className="candidate-details-row">
                                      <div className="candidate-details-cell">Experience: <span className="experience-years">{output.experience_years}</span></div>
                                      <div className="candidate-details-cell">Resume: <span className="resume-filename">{output.filename}</span></div>
                                      <div className="candidate-details-cell">Education: <span className="education">{output.education}</span></div>
                                    </div>
                                  </div>
                                  <div className="candidate-details">
                                    <div className="search-result-detail">Skills: <span>{output.skills}</span></div>
                                  </div>
                                </li>
                              </div>
                            </div>
                          ))}
                        </ul>
                        <div className="pagination">
                          {Array.from({ length: Math.ceil(searchResults.length / resultsPerPage) }, (_, i) => (
                            <button
                              key={i}
                              onClick={() => handlePageChange(i + 1)}
                              className={`pagination-button ${currentPage === i + 1 ? 'active' : ''}`}
                            > 
                              {i + 1}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : ( 
                      <p></p>
                    )}
                  </div>
              )}
            </>
          )}
        <ViewCVModal
          isOpen={modalIsOpen}
          onRequestClose={closeModal}
          filename={currentFile}
          keywordCounts={currentKeywordCounts}
        />
        <ToastContainer/>
      </div>
  );
};

export default TechRequirements;
