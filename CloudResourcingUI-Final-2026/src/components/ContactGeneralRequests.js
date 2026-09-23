import ContactFormGT from "./ContactFormGT";
import books from "./Books.png";

function GeneralRequests() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
        <div class="nav-text">
                <p onClick={() => window.location.href = "/"} class="Page1-descr" >Home</p>
                <p>{'>'}</p>
                <p onClick={() => window.location.href = "/ContactUs/"} class="Page1-descr"> Contact Us</p>
                <p>{'>'}</p>
                <p onClick={() => window.location.href = "/ContactUs/GeneralRequests"} class="Page1-descr"> General Requests</p>
        </div>

        


        <div class="AV-container">
    <div class="light-img2 addedstyling48">
        <img class="addedstyling49" src={books} alt="many black balls together"/>
    </div>
    <h1 class="AV-light-head addedstyling50">General requests.</h1>
    <div class="light-img-and-desc-container addedstyling51">
        <div class="AV-values addedstyling52">
            <p class="AV-light-desc">How can we help you today?</p>
        </div>
        <img class="light-img addedstyling53" src={books} alt="many black balls together"/>
    </div>
</div>

<div class="JS-container JS-light-container">
    <h1 class="JS-head JS-light-head addedstyling54">A member of our team will reach out to you shortly.</h1>
</div>
<ContactFormGT class="SeekerResume-ContactForm"/>

        </>
      );
}

export default GeneralRequests;