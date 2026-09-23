import React, {ChangeEvent, useState} from 'react';
import {FaCaretDown, FaCaretUp} from 'react-icons/fa';
import './smartrecruitment.css';

interface Experience {
    from: string;
    to: string;
};

interface ExperienceProps {
    experience: Experience;
    handleExperienceChange: (field: keyof Experience, value: string) => void;
};


const ExperienceSection: React.FC<ExperienceProps> = ({experience, handleExperienceChange}) => {
    const [showExperience, setShowExperience] = useState<boolean>(false);
    const toggleExperience = () => {
        setShowExperience(!showExperience);
    }
    return (
        <div className="experience-container">
            <div className='experience-header'>
                <label className="experience-label">Experience</label>
                {/* <div className="toggle-icon" onClick={toggleExperience}>
                    {showExperience ? <FaCaretDown title="Hide Items" /> : <FaCaretUp title="Show Items"/>}
                </div> */}
            </div>
            {showExperience && (
                <div className="experience-grid">
                    <div className="experience-input-container">
                        <label className="experience-input-label">From:</label>
                        <input
                            type="number"
                            value={experience.from}
                            placeholder="Years"
                            min={0}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => handleExperienceChange('from', e.target.value)}
                            className="experience-input"
                        />
                    </div>
                    <div className="experience-input-container">
                        <label className="experience-input-label">To:</label>
                        <input
                            type="number"
                            value={experience.to}
                            placeholder="Years"
                            min={0}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => handleExperienceChange('to', e.target.value)}
                            className="experience-input"
                        />
                    </div>
                </div>
            )}
            <div className="toggle-icon" onClick={toggleExperience}>
                {showExperience ? <FaCaretDown title="Hide Items" /> : <FaCaretUp title="Show Items"/>}
            </div>
        </div>
    );
};

export default ExperienceSection;