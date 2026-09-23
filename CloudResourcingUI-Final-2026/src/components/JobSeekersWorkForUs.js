import ContactFormCR from './ContactFormCR';
import flowers from './BlueFlowers.png';

function SeekersWorkForUs() {
    return(
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
         <div class="nav-text">
            <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers"} class="Page1-descr"> Job Seekers</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers/WorkForUs"} class="Page1-descr"> Work For Cloud Resourcing</p>
    </div>

    <div class="addedstyling110 AV-container">
    <div class="addedstyling111 light-img2">
        <img class="addedstyling112" src={flowers} alt="many black balls together"/>
    </div>
    <h1 class="AV-light-head">Join us today.</h1>
    <div class="light-img-and-desc-container">
        <div class="addedstyling113 AV-values">
            <p class="AV-light-desc">Step into a vibrant and innovative atmosphere by joining us at Cloud Resourcing. Explore fulfilling career paths where your skills are valued, and together, let's shape the future of work.</p>
        </div>
        <img class="addedstyling114 light-img" src={flowers} alt="many black balls together"/>
    </div>
</div>
<div class="addedstyling115 JS-container JS-light-container">
    <h1 class="addedstyling116 JS-head JS-light-head">A member of our team will reach out to you shortly.</h1>
</div>
<ContactFormCR class="SeekerResume-ContactForm"/>

        
        </>
    );
}

export default SeekersWorkForUs;