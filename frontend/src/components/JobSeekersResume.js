import ContactForm from "./ContactForm";

function SeekerResume() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
        <div class="nav-text">
            <p onClick={() => window.location.href = "/"} class="Page1-descr">Home </p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers"} class="Page1-descr"> Job Seekers</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers/SendResume"} class="Page1-descr"> Submit Resume </p>
        </div>
        <div class="addedstyling107 JS-container">
    <h1 class="JS-head">Connect with a recruiter today.</h1>
</div>
<div class="addedstyling108 JS-container JS-light-container">
    <h1 class="addedstyling109 JS-head JS-light-head">Upload your resume.</h1>
</div>
<ContactForm class="SeekerResume-ContactForm"/>

        </>
    );
}

export default SeekerResume;