import employer from "./ManInSuit.jpg";
import employee from "./GlassesOnLaptop.webp";
import general from "./PeopleLaughing.jpg";
import { faEnvelope } from "@fortawesome/free-solid-svg-icons";
import { faLocationDot } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

function Contact() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
            <div class="nav-text">
                <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
                <p>{'>'}</p>
                <p onClick={() => window.location.href = "/ContactUs/"} class="Page1-descr"> Contact Us</p>
            </div>

            <div class="JS-container addedstyling31">
    <h1 class="JS-head">Reach out to us.</h1>
</div>

<div class="next-step addedstyling32">
    <h1 class="step-text Contact-img-head addedstyling33">How can we help you today?</h1>
    <div class="img-container img-container2">
        <div class="addedstyling34">
            <img onClick={() => window.location.href = "/JobSeekers/SendResume"} class="img-resume" src={employee} alt="grey laptop"/>
            <p class="Page1-descr" onClick={() => window.location.href = "/JobSeekers/SendResume"}>I am a job seeker.</p>
        </div>
        <div class="addedstyling34">
            <img onClick={() => window.location.href = "/ContactUs/GeneralRequests"} class="Contact-img img-resume" src={general} alt="lone marble"/>
            <p onClick={() => window.location.href = "/ContactUs/GeneralRequests"} class="Contact-img Page1-descr">I have a general request.</p>
        </div>
        <div class="addedstyling34">
            <img onClick={() => window.location.href = "/Employers/HireTalent"} class="Contact-img img-resume" src={employer} alt="grey employer suit with pink card coming out of pocket"/>
            <p onClick={() => window.location.href = "/Employers/HireTalent"} class="Contact-img Page1-descr">I am an employer.</p>
        </div>
    </div>
</div>

<div class="JS-container addedstyling35">
    <h1 class="JS-head">Prefer meeting in person? No problem.</h1>
    <div class="JS-div">
        <p class="JS-desc">We are here for you. Click the button to find a nearby location and meet us in person. Your convenience is our priority.</p>
        <button onClick={() => window.location.href = "/AboutUs/OfficeLocations"} class="JS-button">Find a Location</button>
    </div>
</div>

            <div class="JS-container addedstyling36 JS-light-container">
                <h1 class="JS-head JS-light-head">Cloud resourcing head offices.</h1>
                <div class="address-and-email addedstyling37">
                    <div>
                        <div class="addedstyling38">
                            <FontAwesomeIcon class="JS-desc addedstyling39 JS-light-desc"  icon={faLocationDot} />
                            <h4 class="JS-desc addedstyling40 JS-light-desc">Office Locations:</h4>
                        </div>
                        <p class="JS-desc JS-light-desc">200 Front St. W., Toronto, ON, Canada</p>
                        <p class="JS-desc JS-light-desc">9621 W Avondale Cir, Ypsilanti, MI 48198, USA</p>
                    </div>
                    <div>
                        <div class="addedstyling38">
                            <FontAwesomeIcon class="JS-desc JS-light-desc" style={{height: '60px', marginBottom: '0'}} icon={faEnvelope} />
                            <h4 class="JS-desc addedstyling42 JS-light-desc">Email:</h4>
                        </div>
                        <p class="JS-desc JS-light-desc">jobs@cloudresourcing.net</p>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Contact;