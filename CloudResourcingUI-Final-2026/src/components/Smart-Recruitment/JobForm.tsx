/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the form for recruiters to input the job title and description
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: January 22nd, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
//Imported Libraries
import React, {FormEvent, useState, useEffect, useRef} from "react";
import { FaSearch, FaCaretDown, FaCaretUp } from 'react-icons/fa';
import { HistoryRecord, TechnologyRequirement } from './type.ts';
import {Tooltip} from "react-tooltip"
import 'bootstrap/dist/css/bootstrap.min.css';
import './smartrecruitment.css';

//Interface for the properties of the JobForm function
interface JobFormProps {
    jobTitle: string;
    description: string;
    jobUrl: string;
    setJobTitle: (jobTitle: string) => void;
    setDescription: (description: string) => void;
    setJobUrl: (jobUrl: string) => void;
    handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
    onReset: () => void;
    fetchBooleanPairsAgain: () => void; 
    fetchJobDescription: (jobTitle: string, setDescription: (description: string) => void) => Promise<void>;
    records: HistoryRecord[];
    viewHistory: (indexOrRecord: number | HistoryRecord) => void;
    getBooleanHistory: (jobTitle: string) => Promise<HistoryRecord[] | null>; 
    getRecentBooleanHistory: () => void;
    showHistory: boolean;
    setShowHistory: (showHistory: boolean) => void;
    searchVisible: boolean;
    setSearchVisible: (searchVisible: boolean) => void;
}

//Function that returns the JobForm component
const JobForm: React.FC<JobFormProps> = ({
    jobTitle,
    description,
    jobUrl,
    setJobTitle,
    setDescription,
    setJobUrl,
    handleSubmit,
    onReset,
    fetchBooleanPairsAgain,
    fetchJobDescription,
    getBooleanHistory,
    viewHistory,
    records,
    getRecentBooleanHistory,
    showHistory,
    setShowHistory,
    searchVisible,
    setSearchVisible
}) => {
    const [showUrlSearch, setShowUrlSearch] = useState<boolean>(true);
    const descriptionRef = useRef<HTMLDivElement>(null);
    const [searchInput, setSearchInput] = useState<string>('');
    const [searchResult, setSearchResult] = useState<HistoryRecord[] | null>(null);
    // const [searchVisible, setSearchVisible] = useState<boolean>(false);
    const [hasFetchedHistory, setHasFetchedHistory] = useState<boolean>(false);
    
    
    // const handleJobUrlSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    //     e.preventDefault();
    //     await handleFindJobInfo();
    // }
    const toggleCandidates = () => {
        setShowUrlSearch(!showUrlSearch);
    }

    const handleDescriptionChange = () => {
        if (descriptionRef.current) {
          setDescription(descriptionRef.current.innerHTML);
        }
    };
    
    useEffect(() => {
        if (descriptionRef.current) {
          descriptionRef.current.innerHTML = description;
        }
    }, [description]);

    const handleFetchJobDescription = async () => {
        await fetchJobDescription(jobTitle, setDescription);
    };

    const handleSearch = async () => {
        const result = await getBooleanHistory(searchInput);
        if (result) {
            setSearchResult(result); // Ensure result is an array
        } else {
            alert('No records found for the given job title');
        }
    };

    useEffect(() => {
        if (!hasFetchedHistory) {
          getRecentBooleanHistory();
          setHasFetchedHistory(true);
        }
    }, [getRecentBooleanHistory, hasFetchedHistory]);
    
    // const handleView = (record: HistoryRecord) => {
    //     if (searchResult && searchResult[0]) {
    //         viewHistory(searchResult[0]);
    //         setSearchResult(null);
    //         setSearchInput('');
    //     }
    // };

    const handleView = (record: HistoryRecord) => {
        viewHistory(record);
        setSearchResult(null);
        setSearchInput('');
        setSearchVisible(false);
    };
    
    const handleCancel = () => {
        setSearchResult(null);
        setSearchInput('');
    };
    
    const formatTooltipContentSearch = (content: string | undefined) => {
        if (!content) {
            return '';
        }
        const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/g;
        return content.replace(regex, "<br>");
    };

    const formatTooltipContent = (content: string) => { // Function to format the tooltip content
        const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/g;
        return content.replace(regex, "<br>");
      };

    const toggleHistory = () => {
        setShowHistory(!showHistory);
        setSearchVisible(false)
    }

    const handleSearchIconClick = () => {
        setSearchVisible(!searchVisible);
        setShowHistory(false);
    }

    return (
        <section className="job-form-section">
            <div className="job-form-container">
                <form onSubmit={handleSubmit}>
                    {/* <div className="mb-4">
                        <div className="job-url-section">
                            <label className="job-form-label">Job URL</label>
                            <div className="toggle-icon" onClick={toggleCandidates}>
                                {showUrlSearch ? <FaCaretDown title="Hide Items" /> : <FaCaretUp title="Show Items"/>}
                            </div>
                        </div>
                        {showUrlSearch && (
                            <div>
                                <input
                                    type="text"
                                    value={jobUrl}
                                    onChange={(e) => { setJobUrl(e.target.value); } }
                                    className="job-form-input" />
                                <div className="find-button">
                                    <button className="job-fetch-button" onClick={handleJobUrlSubmit}>Fetch Job Info</button>
                                </div>
                            </div>
                        )}
                    </div> */}
                    {/* <div className="find-button">
                        <button className="job-fetch-button" onClick={handleJobUrlSubmit}>Fetch Job Info</button>
                    </div> */}
                    
                    {/* Job Title */}
                    <div className="mb-4">
                        <label className="job-form-label">Job Title</label>
                        <input
                            type="text"
                            value={jobTitle}
                            onChange={(e) => {
                                setJobTitle(e.target.value)
                                fetchBooleanPairsAgain()
                            }}
                            className="job-form-input"
                            required
                        />
                        {/* <div className="find-button">
                            <button className="job-fetch-button" onClick={handleFetchJobDescription}>Fetch Job Info</button>
                        </div> */}
                    </div>
                    
                    {/* Job Description */}
                    <div className="mb-4">
                        <label className="job-form-label">Job Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="job-form-textarea"
                            required>
                        </textarea>
                        {/* <div
                            ref={descriptionRef}
                            className="form-control" // Bootstrap class for input
                            style={{ height: 'auto', minHeight: '100px', whiteSpace: 'pre-wrap' }}
                            contentEditable
                            onInput={handleDescriptionChange}
                        ></div> */}
                    </div>

                    {/* Submit Button */}
                    <div className="button-group">
                        <button
                            type="submit"
                            className="job-form-button"
                        >
                            Submit
                        </button>
                        <button
                            onClick={onReset}
                            className="reset-button"
                        >
                            Reset
                        </button>
                    </div>
                </form>
                <div className="history-records-container">
                    <div className="search-title-dropdown">
                        <div className="search-and-title">
                            <label className='history-title'>History</label>
                            <FaSearch className="icon-button" onClick={handleSearchIconClick} />
                            {searchVisible && (
                                <>
                                    <input
                                        type="text"
                                        value={searchInput}
                                        onChange={(e) => setSearchInput(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                handleSearch();
                                            }
                                        }}
                                        placeholder="Search Job Title"
                                        className="search-input"
                                    />
                                </>
                            )}
                        </div>
                        <div className="toggle-icon" onClick={toggleHistory}>
                            {showHistory ? <FaCaretDown title="Hide History" /> : <FaCaretUp title="Show History"/>}
                        </div>
                    </div>
                    {/* <div className="search-record-container"> */}
                        {searchVisible && (
                            <>
                                <div className="search-history-record-header">
                                    <span className="search-history-record-header-title">Job Title</span>
                                    <span className="search-history-record-header-description">Job Description</span>
                                    <span className="search-history-record-header-phrase">Boolean Phrase</span>
                                </div>
                                <div className="search-record-container">
                                    <div className="search-function-record">
                                        {/* <input
                                            type="text"
                                            value={searchInput}
                                            onChange={(e) => setSearchInput(e.target.value)}
                                            placeholder="Search Job Title"
                                            className="search-input"
                                        /> */}
                                        {/* <button onClick={handleSearch} className="search-button">Search</button> */}
                                        {searchResult && searchResult.map((result, index) => (
                                            
                                            <div key={index} className="search-record">
                                                <div className="search-history-record-item-title">
                                                    <span 
                                                        className="search-history-record-value"
                                                        data-tooltip-id={`tooltip-search-description-${index}`}
                                                        data-tooltip-content={formatTooltipContentSearch(result.jobTitle)}
                                                    >
                                                        {result.jobTitle}
                                                    </span>
                                                    <Tooltip id={`tooltip-search-description-${index}`} place="top" variant="dark" className="custom-tooltip" />
                                                </div>
                                                <div className="search-history-record-item-description">
                                                    <span
                                                        className="history-record-input"
                                                        data-tooltip-id={`tooltip-search-description-${index}`}
                                                        data-tooltip-content={formatTooltipContentSearch(result.jobDescription)}
                                                    >
                                                        {result.jobDescription}
                                                    </span>
                                                    <Tooltip id={`tooltip-search-description-${index}`} place="top" variant="dark" className="custom-tooltip" />
                                                </div>
                                                <div className="search-history-record-item-phrase">
                                                    <span
                                                        className="history-record-input"
                                                        data-tooltip-id={`tooltip-search-phrase-${index}`}
                                                        data-tooltip-content={formatTooltipContentSearch(result.booleanPhrase)}
                                                    >
                                                        {result.booleanPhrase}
                                                    </span>
                                                    <Tooltip id={`tooltip-search-phrase-${index}`} place="top" variant="dark" className="custom-tooltip" />
                                                </div>
                                                <div className="search-buttons">
                                                    <button onClick={() => handleView(result)} className="view-button">View</button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    {showHistory && (
                        <>
                            <div className="history-record-header">
                                <span className="history-record-header-title">Job Title</span>
                                <span className="history-record-header-description">Job Description</span>
                                <span className="history-record-header-phrase">Boolean Phrase</span>
                            </div>
                            {records.map((record, index) => (
                                <div key={index} className="history-record">
                                    {/* <label className="history-record-title">Job Title:</label> */}
                                    <div className="history-record-item-title">
                                       <span
                                            className="history-record-value"
                                            data-tooltip-id={`tooltip-search-description-${index}`}
                                            data-tooltip-content={formatTooltipContent(record.jobTitle)}
                                        >
                                            {record.jobTitle}
                                        </span>
                                        <Tooltip id={`tooltip-search-description-${index}`} place="top" variant="dark" className="custom-tooltip" />        
                                    </div>
                                    <div className="history-record-item-description">
                                        <span
                                            className="history-record-input"
                                            data-tooltip-id={`tooltip-search-description-${index}`}
                                            data-tooltip-content={formatTooltipContent(record.jobDescription)}
                                        >
                                            {record.jobDescription}
                                        </span>
                                        <Tooltip id={`tooltip-search-description-${index}`} place="top" variant="dark" className="custom-tooltip" />
                                    </div>
                                    <div className="history-record-item-phrase">
                                        <span
                                            className="history-record-input"
                                            data-tooltip-id={`tooltip-search-phrase-${index}`}
                                            data-tooltip-content={formatTooltipContent(record.booleanPhrase)}
                                        >
                                            {record.booleanPhrase}
                                        </span>
                                        <Tooltip id={`tooltip-search-phrase-${index}`} place="top" variant="dark" className="custom-tooltip" />
                                    </div>
                                    {/* <Tooltip id={`tooltip-${index}`} place="top" variant="dark" /> */}
                                    <button onClick={() => viewHistory(index)} className='view-button'>View</button>
                                </div>
                            ))}
                        </>
                    )}
                </div>
            </div>
        </section>
    )
}

export default JobForm;