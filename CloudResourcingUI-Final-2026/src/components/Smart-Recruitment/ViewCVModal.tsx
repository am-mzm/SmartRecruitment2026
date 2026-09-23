/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: Handles the technology requirements component for recruiters to input the technology requirements after clicking the submit button
 *                          Created Date: March 18, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: March 20, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
import React, {useState, useEffect, useRef} from "react";
import { Modal} from "react-bootstrap";
import 'bootstrap/dist/css/bootstrap.min.css';
import './smartrecruitment.css';
import { renderAsync } from "docx-preview";
import {Tooltip} from "react-tooltip";

interface ViewCVModalProps {
    isOpen: boolean;
    onRequestClose: () => void;
    filename: string | null;
    // keywordCounts: { [key: string]: number } | null;
    keywordCounts: { 
        [key: string]: { 
            count: number; 
            related_keywords: { keyword: string; count: number }[]; 
        } 
    } | null;
}

const ViewCVModal: React.FC<ViewCVModalProps> = ({ isOpen, onRequestClose, filename, keywordCounts }) => {
    
    const docxContainerRef = useRef<HTMLDivElement>(null); // Reference for DOCX preview container
    
    const [verifiedKeywordCounts, setVerifiedKeywordCounts] = useState<{
        [key: string]: { 
            total: number; 
            related: { [key: string]: number }; 
        }; 
    } | null>(null);
        
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden"; 
        } else {
            document.body.style.overflow = "auto";
        }
        return () => {
            document.body.style.overflow = "auto";
        };
    }, [isOpen]);

    const isDocx = filename && (filename.endsWith('.docx') || filename.endsWith('.pdf'));
    const docUrl = filename ? `${process.env.REACT_APP_PYTHON_ROUTE}/view-resume/${filename}` : '';

    const highlightKeywords = (
        text: string,
        keywords: { [key: string]: { related_keywords: { keyword: string }[] } }
    ): { highlightedText: string; keywordCounts: { [key: string]: { total: number; related: { [key: string]: number } } } } => {
        const keywordCounts: { [key: string]: { total: number; related: { [key: string]: number } } } = {};
    
        Object.entries(keywords).forEach(([mainKeyword, { related_keywords }]) => {
            const relatedCounts: { [key: string]: number } = {};
            let totalCount = 0;
    
            // Combine only related keywords (exclude the main keyword unless explicitly listed as related)
            const allKeywords = related_keywords.map(rk => rk.keyword);
            const escapedKeywords = allKeywords.map(kw => kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
            const relatedKeywordsRegex = new RegExp(`\\b(${escapedKeywords.join("|")})\\b`, "gi");
    
            // Match related keywords in the text
            const relatedMatches = text.match(relatedKeywordsRegex) || [];
            relatedMatches.forEach(match => {
                const normalizedMatch = match.toLowerCase();
                related_keywords.forEach(({ keyword }) => {
                    if (normalizedMatch === keyword.toLowerCase()) {
                        relatedCounts[keyword] = (relatedCounts[keyword] || 0) + 1;
                        totalCount++;
                    }
                });
            });
    
            // console.log(`Main Keyword: "${mainKeyword}"`);
            // console.log(`Related Keywords: ${JSON.stringify(related_keywords.map(rk => rk.keyword))}`);
            // console.log(`Related Counts: ${JSON.stringify(relatedCounts)}`);
            // console.log(`Total Count for "${mainKeyword}": ${totalCount}`);
    
            // Highlight the keywords in the text
            text = text.replace(relatedKeywordsRegex, (match) => `<span class="highlight">${match}</span>`);
    
            // Store the counts
            keywordCounts[mainKeyword] = {
                total: totalCount,
                related: relatedCounts,
            };
        });
    
        // console.log("Final keyword counts:", JSON.stringify(keywordCounts, null, 2));
        return { highlightedText: text, keywordCounts };
    };

    useEffect(() => {
        let isMounted = true;
    
        if (isDocx && filename && docxContainerRef.current) {
            fetch(docUrl)
                .then(res => {
                    if (!res.ok) {
                        throw new Error(`Failed to fetch DOCX file: ${res.statusText}`);
                    }
                    return res.blob();
                })
                .then(blob => {
                    if (isMounted && docxContainerRef.current) {
                        docxContainerRef.current.innerHTML = "";
                        renderAsync(blob, docxContainerRef.current)
                            .then(() => {
                                if (keywordCounts && docxContainerRef.current) {
                                    const content = docxContainerRef.current.innerHTML;
    
                                    // Highlight keywords and count occurrences
                                    const { highlightedText, keywordCounts: updatedCounts } = highlightKeywords(content, keywordCounts);
    
                                    // Update the DOM with highlighted text
                                    docxContainerRef.current.innerHTML = highlightedText;
    
                                    // Update the verified keyword counts
                                    setVerifiedKeywordCounts(updatedCounts);
                                }
                            })
                            .catch(renderError => console.error("Error rendering DOCX content:", renderError));
                    }
                })
                .catch(fetchError => console.error("Error loading DOCX file:", fetchError));
        }
    
        return () => {
            isMounted = false;
        };
    }, [docUrl, filename, isDocx, keywordCounts]);

    return (
        <Modal
            show={isOpen}
            onHide={onRequestClose}
            size="xl"
            centered
            backdrop="static" 
            keyboard={false}   
            className="custom-modal"  // Apply custom class
        >
            <Modal.Header closeButton>
                <Modal.Title>
                {isDocx && verifiedKeywordCounts && Object.keys(verifiedKeywordCounts).length > 0 && (
                    <div className="keyword-counts-container">
                        <h5>Verified Keywords</h5>
                        <div className="keyword-counts">
                            {Object.entries(verifiedKeywordCounts)
                                .sort((a, b) => b[1].total - a[1].total)
                                .map(([keyword, { total, related }]) => {
                                    const relatedKeywordsContent = Object.entries(related || {})
                                        .map(([relatedKeyword, count]) => `${relatedKeyword}: ${count}`)
                                        .join(", ");

                                    return (
                                        <span
                                            key={keyword}
                                            className="keyword-item"
                                            data-tooltip-id="keyword-tooltip"
                                            data-tooltip-content={
                                                Object.keys(related || {}).length > 0
                                                    ? `${relatedKeywordsContent}`
                                                    : "No related keywords"
                                            }
                                        >
                                            {keyword}: {total}
                                        </span>
                                    );
                                })}
                            <Tooltip id="keyword-tooltip" place="top" variant="dark" />
                        </div>
                    </div>
                )}
                </Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {isDocx && <div ref={docxContainerRef} className="docx-preview-container" />}
            </Modal.Body>
        </Modal>
    );
};

export default ViewCVModal;