/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the component for processing boolean values and displaying the processed string
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: January 22nd, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
import React, {useEffect, useState} from "react";
import {FaCopy} from "react-icons/fa";
import './smartrecruitment.css';
import { HiOutlineSave } from "react-icons/hi";

interface BooleanStringProps {
    technologyRequirements: {
        BOOLEANVALUE: string;
    }[];
    // booleanPhrase: string;
    // setBooleanPhrase: (booleanPhrase: string) => void;
    jobCode: string | null;
    setJobCode: (jobCode: string) => void;
    mergedArray: string[]
    saveBooleanHistory: () => void;
    handleRetrievePhrase: (processedString: string) => void;
    getRecentBooleanHistory: () => void;
    processedString: string;
    setProcessedString: (processedString: string) => void;
    // mergeNameWeightages: () => void;

}

const BooleanString: React.FC<BooleanStringProps> = ({technologyRequirements, saveBooleanHistory, handleRetrievePhrase, getRecentBooleanHistory, processedString, setProcessedString}) => {
    // const [processedString, setProcessedString] = useState<string>("");

    // const processBooleanValues = () => { // Function to process the boolean values
    //     const uniqueValues = new Set(); // Set to store unique values(not repeated)
    //     const processed = technologyRequirements
    //     .map(tech => { // Maps the technology requirements
    //         const values = tech.BOOLEANVALUE.split(',') // Splits the boolean values
    //             .map(val => val.replace(/\\/g, '').trim()) // Removes the backslashes and trims the values
    //             .filter(val => {
    //                 if(uniqueValues.has(val)) { // Checks if the value is unique
    //                     return false;
    //                 } else{
    //                     uniqueValues.add(val); // Adds the value to the set
    //                     return true;
    //                 }
    //         })
    //         return values.length > 0 ? `(${values.map(val => `${val}`).join(' OR ')})` : null; // Returns the values and joins them with ORs.
    //     })
    //     .filter(Boolean) 
    //     .join(' AND '); // Joins the different boolean values with ANDs
    
    //     setProcessedString(processed);
    //     // setBooleanPhrase(processed);
    //     // console.log("Stored Boolean Phrase: ", booleanPhrase )
    // }

    useEffect(() => {
        const processBooleanValues = () => { // Function to process the boolean values
            const uniqueValues = new Set(); // Set to store unique values(not repeated)
            const processed = technologyRequirements
                .map(tech => { // Maps the technology requirements
                    const values = tech.BOOLEANVALUE.split(',') // Splits the boolean values
                        .map(val => val.replace(/\\/g, '').trim()) // Removes the backslashes and trims the values
                        .filter(val => {
                            if (uniqueValues.has(val)) { // Checks if the value is unique
                                return false;
                            } else {
                                uniqueValues.add(val); // Adds the value to the set
                                return true;
                            }
                        });
                    return values.length > 0 ? `(${values.map(val => `${val}`).join(' OR ')})` : null; // Returns the values and joins them with ORs.
                })
                .filter(Boolean)
                .join(' AND '); // Joins the different boolean values with ANDs
    
            setProcessedString(processed);
        };
    
        processBooleanValues();
    }, [technologyRequirements, setProcessedString]);

    useEffect(() => {
        handleRetrievePhrase(processedString);
    }, [processedString, handleRetrievePhrase])

    const copyToClipboard = () => { // Function to copy the processed string to the clipboard
        navigator.clipboard.writeText(processedString).then(() => {
        //   alert('Boolean Phrase Copied to Clipboard and Saved to History Records');
        }).catch(err => {
          console.error('Error copying to clipboard', err);
        })
    }

    const handleCopyAndSave = () => {
        copyToClipboard();
        saveHistory();
        getRecentBooleanHistory();
    }

    const timeout = (delay: number) => {
        return new Promise(res => setTimeout(res, delay));
    };

    const saveHistory = async () => {
        await saveBooleanHistory();
    }



    return (
        <div className="processed-string-section">
            {/* <div className="button-container">
                <button
                    onClick={processBooleanValues}
                    className="boolean-string-button"
                >
                    Process Boolean Values
                </button>
            </div> */}
            {processedString && (
                <div className="processed-string-container">
                    <h3 className="processed-string-title">Processed Boolean Phrase: </h3>
                    <div className="flex items-center">
                        {/* Text area for the processed string */}
                        <textarea
                            value={processedString}
                            readOnly
                            className="processed-string-textarea"
                        />
                        {/* Copy button */}
                        <div className="boolean-buttons">
                            {/* <button onClick={getRecentBooleanHistory} className="history-button">
                                View History
                            </button> */}
                            {/* <div className="left-space"></div> */}
                            <div className="center-container">
                                <button onClick={handleCopyAndSave} className="copy-button">
                                    <FaCopy className="mr-3" /> Copy/
                                    <HiOutlineSave className="mr-4"/>Save
                                </button>
                            </div>
                            {/* <HiOutlineSave onClick={() => saveHistory()} className="save-everything" /> */}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default BooleanString;
