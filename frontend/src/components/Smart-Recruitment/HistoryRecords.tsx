import React, {useState} from 'react';
import { FaSearch } from 'react-icons/fa';
import { HistoryRecord, TechnologyRequirement } from './type.ts';
import {Tooltip} from "react-tooltip"

// interface TechnologyRequirement {
//   BOOLEANNAME: string;
//   BOOLEANVALUE: string;
// }

// interface HistoryRecord {
//   jobTitle: string;
//   jobDescription: string;
//   booleanPhrase: string;
//   technologyRequirements: TechnologyRequirement[];
// }

interface HistoryRecordsProps {
  records: HistoryRecord[];
  viewHistory: (indexOrRecord: number | HistoryRecord) => void;
  getBooleanHistory: (jobTitle: string) => Promise<HistoryRecord | null>;
  // viewOneHistory: (record: HistoryRecord) => void;
}

const HistoryRecords: React.FC<HistoryRecordsProps> = ({ records, viewHistory, getBooleanHistory }) => {
  const [searchInput, setSearchInput] = useState<string>('');
  const [searchResult, setSearchResult] = useState<HistoryRecord | null>(null);
  const [searchVisible, setSearchVisible] = useState<boolean>(false);

  const handleSearch = async () => {
    const result = await getBooleanHistory(searchInput);
    if (result) {
      setSearchResult(result);
    } else {
      alert('No records found for the given job title');
    }
  };

  const handleView = () => {
    if (searchResult) {
      viewHistory(searchResult);
      setSearchResult(null);
      setSearchInput('');
    }
  };

  const handleCancel = () => {
    setSearchResult(null);
    setSearchInput('');
  };

  const formatTooltipContent = (content: string) => { // Function to format the tooltip content
    const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/g;
    return content.replace(regex, "<br>");
  };


  return (
    <section className="history-records-section">
      <div className="history-records-container">
        <label className='history-title'>Recent Boolean History</label>
        <div className="history-record-header">
          <span className="history-record-header-title">Job Title</span>
          <span className="history-record-header-description">Job Description</span>
          <span className="history-record-header-phrase">Booelan Phrase</span>
          {/* <span className="history-record-header-action"></span> Empty for spacing */}
        </div>
        {records.map((record, index) => (
          <div key={index} className="history-record">
            {/* <label className="history-record-title">Job Title:</label> */}
            <div className="history-record-item-title">
              {/* <label className="history-record-title">Job Title:</label> */}
              {/* <input
                type="text"
                value={record.jobTitle}
                readOnly
                className="history-record-value"
              /> */}
              <span className="history-record-value">{record.jobTitle}</span>          
            </div>
            <div className="history-record-item-description">
              {/* <label className="history-record-title">Job Description:</label> */}
              <input
                type="text"
                value={record.jobDescription}
                readOnly
                className="history-record-input"
                data-tooltip-id={`tooltip-${index}`}
                data-tooltip-content={formatTooltipContent(record.jobDescription)}
              />
              {/* <Tooltip id={`tooltip-${index}`} place="top" variant="dark" /> */}
            </div>
            <div className="history-record-item-phrase">
              {/* <label className="history-record-title">Boolean Phrase:</label> */}
              <input
                type="text"
                value={record.booleanPhrase}
                readOnly
                className="history-record-input"
                data-tooltip-id={`tooltip-${index}`}
                data-tooltip-content={formatTooltipContent(record.booleanPhrase)}
              />
              {/* <Tooltip id={`tooltip-${index}`} place="top" variant="dark" /> */}
            </div>
            {/* <Tooltip id={`tooltip-${index}`} place="top" variant="dark" /> */}
            <button onClick={() => viewHistory(index)} className='view-button'>View</button>
          </div>
        ))}
        <div className="search-record-container">
          <FaSearch className="icon-button" onClick={() => setSearchVisible(!searchVisible)} />
          {searchVisible && (
          <>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search Job Title"
              className="search-input"
            />
            <button onClick={handleSearch} className="search-button">Search</button>

            {searchResult && (
              <div className="search-record">
                {/* <div className="history-record-item-title">
                  <span className="history-record-value">{searchResult.jobTitle}</span>
                </div> */}
                <div className="search-history-record-item-description">
                  {/* <input
                    type="text"
                    value={searchResult.jobDescription}
                    readOnly
                    className="history-record-input"
                    data-tooltip-id={`tooltip-search-description`}
                    data-tooltip-content={formatTooltipContent(searchResult.booleanPhrase)}
                  /> */}
                  <span
                    className="history-record-input"
                    data-tooltip-id={`tooltip-search-description`}
                    data-tooltip-content={formatTooltipContent(searchResult.jobDescription)}
                  >
                    {searchResult.jobDescription}
                  </span>
                  <Tooltip id={`tooltip-search-description`} place="top" variant="dark" className="custom-tooltip" />
                </div>
                <div className="search-history-record-item-phrase">
                  {/* <input
                    type="text"
                    value={searchResult.booleanPhrase}
                    readOnly
                    className="history-record-input"
                    data-tooltip-id={`tooltip-search-phrase`}
                    data-tooltip-content={formatTooltipContent(searchResult.booleanPhrase)}
                  /> */}
                  <span
                    className="history-record-input"
                    data-tooltip-id={`tooltip-search-phrase`}
                    data-tooltip-content={formatTooltipContent(searchResult.booleanPhrase)}
                  >
                    {searchResult.booleanPhrase}
                  </span>
                  <Tooltip id={`tooltip-search-phrase`} place="top" variant="dark" className="custom-tooltip" />
                </div>
                <div className="search-buttons">
                  <button onClick={handleView} className="view-button">View</button>
                  <button onClick={handleCancel} className="cancel-button">Cancel</button>
                </div>
              </div>
            )}
          </>
          )}
        </div>
      </div>
    </section>
  );
};

export default HistoryRecords;