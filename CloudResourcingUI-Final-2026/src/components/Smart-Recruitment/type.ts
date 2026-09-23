export interface TechnologyRequirement {
  BOOLEANNAMEVALUEPAIRID?: number;
  BOOLEANNAME: string;
  BOOLEANVALUE: string;
  weightage?: string;
  isEditable?: boolean;
  index: number;
}
  
export interface HistoryRecord {
    jobTitle: string;
    jobDescription: string;
    booleanPhrase: string;
    technologyRequirements: TechnologyRequirement[];
}