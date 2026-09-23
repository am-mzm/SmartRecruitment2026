import "./layout.css";
import React from 'react';
import MapComponent from './MapComponent';
import { faEnvelope } from "@fortawesome/free-solid-svg-icons";
import { faLocationDot } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

function Office() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
         <div class="nav-text">
            <p onClick={() => window.location.href = "/"}  class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs"}  class="Page1-descr"> About Us</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs/OfficeLocations"}  class="Page1-descr"> Office Locations</p>
            </div>


            <div class="AV-container">
        <h1 class="AV-light-head">Get in touch today.</h1>
        <div class="JS-container">
            <div class="address-and-email addedstyling16">
                <div>
                    <div class="addedstyling17">
                        <FontAwesomeIcon class="JS-desc addedstyling18" icon={faLocationDot} />
                        <h4 class="JS-desc addedstyling19">Office Locations:</h4>
                    </div>
                    <p class="JS-desc">200 Front St. W., Toronto, ON, Canada</p>
                    <p class="JS-desc">9621 W Avondale Cir, Ypsilanti, MI 48198, USA</p>
                </div>
                <div>
                    <div class="addedstyling17">
                        <FontAwesomeIcon class="JS-desc addedstyling20" icon={faEnvelope} />
                        <h4 class="JS-desc addedstyling19">Email:</h4>
                    </div>
                    <p class="JS-desc">jobs@cloudresourcing.net</p>
                </div>
            </div>
        </div>
    </div>
    <MapComponent />
   
            
        </>
    );

}

export default Office;