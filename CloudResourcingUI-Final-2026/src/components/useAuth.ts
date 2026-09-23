/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment
 *                          Description: This file is used to handle the whether the user is authenticated or not
 *                          Created Date: January 22nd, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: February 4, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/import {useMsal} from "@azure/msal-react";

 const useAuth = () => {
    const {accounts} = useMsal();
    return accounts.length > 0;
}

export default useAuth;