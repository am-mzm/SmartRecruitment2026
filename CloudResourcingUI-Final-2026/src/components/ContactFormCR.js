

import { useRef, useState } from 'react';
import emailjs from '@emailjs/browser';
import "./layout.css";
import { Editor } from '@tinymce/tinymce-react';

/* CONTACT FORM FOR THE JOB SEEKERS - WORK FOR CLOUD RESOURCING PAGE */

function ContactForm() {
  const form = useRef();
  const [message, setMessage] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [mobileNumber, setMobileNumber] = useState('');
  const [resume, setResume] = useState('');
  
  const handleInputChange = (event) => {
    const { value } = event.target;
    if (/^[0-9+\-()]*$/.test(value)) {
      setMobileNumber(value);
    }
  };


  const sendEmail = (e) => {
    e.preventDefault();
    const emailInput = document.getElementsByName('email')[0].value;

    const validateEmail = (email) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    };
  

      if (!validateEmail(emailInput)) {
        alert('Please enter a valid email address.');
      }

     emailjs
    .sendForm('service_0ltuu5k', 'template_tvytzba', form.current, {
      publicKey: 'MklEzlSFxIItnkxOM',
    })
    .then(
      () => {
        console.log('SUCCESS!');
        form.current.reset();
        setMessage('');
        setCharCount(0);
        setResume('');
        setMobileNumber('');
        alert("Email sent successfully.");
        setSelectedPosition('');
        setSelectedDuration('');
      },
      (error) => {
        console.log('FAILED...', error.text);
        alert('Failed to send email. Please try again later.');
      },
    );
    




  };
  

  const handleMessageChange = (e) => {
    setMessage(e.target.value);
    setCharCount(e.target.value.length);
  };

  const [selectedPosition, setSelectedPosition] = useState('');
  const [selectedDuration, setSelectedDuration] = useState('');

  const handlePositionChange = (event) => {
    setSelectedPosition(event.target.value);
  };

  const handleDurationChange = (event) => {
    setSelectedDuration(event.target.value);
  };
  const handleResumeChange = (content) => {
    setResume(content);
  };
  


  return (
    <form onSubmit={sendEmail} ref={form} className="SeekerResumeContactForm">
      <input class="input" type="text" name="form_location" value="Work For Us Request" className='addedstyling46'  />
      <label>First Name*</label>
      <input maxLength='150' class="input" type="text" name="first_name" required placeholder="first name..." />
      <label>Last Name*</label>
      <input maxLength='150' class="input" type="text" name="last_name" required placeholder="last name..." />
      <label>Contact Number*</label>
      <input 
      class="input" 
      type="tel" 
      name="contact_number" 
      required 
      value={mobileNumber}
      onChange={handleInputChange}
      maxLength="20"
      placeholder="number..." />
      <label>Email*</label>
      <input maxLength='150' class="input" type="email" name="email" required placeholder="email..." />
      <label for="country">Country*</label>
      <select required class="crsField form-control" name="country" onchange="loadStates(this.value, 1, '#sub-states-list')">
        <option value="">Select</option>
        <option value="Afghanistan">Afghanistan</option>
        <option value="Aland Islands">Aland Islands</option>
        <option value="Albania">Albania</option>
        <option value="Algeria">Algeria</option>
        <option value="American Samoa">American Samoa</option>
        <option value="Andorra">Andorra</option>
        <option value="Angola">Angola</option>
        <option value="Anguilla">Anguilla</option>
        <option value="Antigua and Barbuda">Antigua and Barbuda</option>
        <option value="Argentina">Argentina</option>
        <option value="Armenia">Armenia</option>
        <option value="Aruba">Aruba</option>
        <option value="Australia">Australia</option>
        <option value="Austria">Austria</option>
        <option value="Azerbaijan">Azerbaijan</option>
        <option value="Bahamas">Bahamas</option>
        <option value="Bahrain">Bahrain</option>
        <option value="Bangladesh">Bangladesh</option>
        <option value="Barbados">Barbados</option>
        <option value="Belarus">Belarus</option>
        <option value="Belgium">Belgium</option>
        <option value="Belize">Belize</option>
        <option value="Benin">Benin</option>
        <option value="Bermuda">Bermuda</option>
        <option value="Bhutan">Bhutan</option>
        <option value="Bolivia">Bolivia</option>
        <option value="Bosnia and Herzegovina">Bosnia and Herzegovina</option>
        <option value="Botswana">Botswana</option>
        <option value="Bouvet Island">Bouvet Island</option>
        <option value="Brazil">Brazil</option>
        <option value="British Indian Ocean Territory">British Indian Ocean Territory</option>
        <option value="British Virgin Islands">British Virgin Islands</option>
        <option value="Brunei">Brunei</option>
        <option value="Bulgaria">Bulgaria</option>
        <option value="Burkina Faso">Burkina Faso</option>
        <option value="Burundi">Burundi</option>
        <option value="CA">Canada</option>
        <option value="Cambodia">Cambodia</option>
        <option value="Cameroon">Cameroon</option>
        <option value="Canada">Canada</option>
        <option value="Cape Verde">Cape Verde</option>
        <option value="Cayman Islands">Cayman Islands</option>
        <option value="Central African Republic">Central African Republic</option>
        <option value="Chad">Chad</option>
        <option value="Chile">Chile</option>
        <option value="China">China</option>
        <option value="Christmas Island">Christmas Island</option>
        <option value="Cocos Islands">Cocos Islands</option>
        <option value="Colombia">Colombia</option>
        <option value="Comoros">Comoros</option>
        <option value="Cook Islands">Cook Islands</option>
        <option value="Costa Rica">Costa Rica</option>
        <option value="Croatia">Croatia</option>
        <option value="Cuba">Cuba</option>
        <option value="Cyprus">Cyprus</option>
        <option value="Czech Republic">Czech Republic</option>
        <option value="Democratic Republic of the Congo">Democratic Republic of the Congo</option>
        <option value="Denmark">Denmark</option>
        <option value="Djibouti">Djibouti</option>
        <option value="Dominica">Dominica</option>
        <option value="Dominican Republic">Dominican Republic</option>
        <option value="East Timor">East Timor</option>
        <option value="Ecuador">Ecuador</option>
        <option value="Egypt">Egypt</option>
        <option value="El Salvador">El Salvador</option>
        <option value="Equatorial Guinea">Equatorial Guinea</option>
        <option value="Eritrea">Eritrea</option>
        <option value="Estonia">Estonia</option>
        <option value="Ethiopia">Ethiopia</option>
        <option value="Falkland Islands">Falkland Islands</option>
        <option value="Faroe Islands">Faroe Islands</option>
        <option value="Fiji">Fiji</option>
        <option value="Finland">Finland</option>
        <option value="France">France</option>
        <option value="French Guiana">French Guiana</option>
        <option value="French Polynesia">French Polynesia</option>
        <option value="French Southern Territories">French Southern Territories</option>
        <option value="Gabon">Gabon</option>
        <option value="Gambia">Gambia</option>
        <option value="Georgia">Georgia</option>
        <option value="Germany">Germany</option>
        <option value="Ghana">Ghana</option>
        <option value="Gibraltar">Gibraltar</option>
        <option value="Glendale, California">Glendale, California</option>
        <option value="Greece">Greece</option>
        <option value="Greenland">Greenland</option>
        <option value="Grenada">Grenada</option>
        <option value="Guadeloupe">Guadeloupe</option>
        <option value="Guam">Guam</option>
        <option value="Guatemala">Guatemala</option>
        <option value="Guernsey">Guernsey</option>
        <option value="Guinea">Guinea</option>
        <option value="Guinea-Bissau">Guinea-Bissau</option>
        <option value="Guyana">Guyana</option>
        <option value="Haiti">Haiti</option>
        <option value="Heard Island and McDonald Islands">Heard Island and McDonald Islands</option>
        <option value="Honduras">Honduras</option>
        <option value="Hong Kong">Hong Kong</option>
        <option value="Hungary">Hungary</option>
        <option value="Iceland">Iceland</option>
        <option value="India">India</option>
        <option value="Indonesia">Indonesia</option>
        <option value="Iran">Iran</option>
        <option value="Iraq">Iraq</option>
        <option value="Ireland">Ireland</option>
        <option value="Isle of Man">Isle of Man</option>
        <option value="Israel">Israel</option>
        <option value="Italy">Italy</option>
        <option value="Ivory Coast">Ivory Coast</option>
        <option value="Jamaica">Jamaica</option>
        <option value="Japan">Japan</option>
        <option value="Jersey">Jersey</option>
        <option value="Jordan">Jordan</option>
        <option value="Kazakhstan">Kazakhstan</option>
        <option value="Kenya">Kenya</option>
        <option value="Kiribati">Kiribati</option>
        <option value="Kosovo">Kosovo</option>
        <option value="Kuwait">Kuwait</option>
        <option value="Kyrgyzstan">Kyrgyzstan</option>
        <option value="Laos">Laos</option>
        <option value="Latvia">Latvia</option>
        <option value="Lebanon">Lebanon</option>
        <option value="Lesotho">Lesotho</option>
        <option value="Liberia">Liberia</option>
        <option value="Libya">Libya</option>
        <option value="Liechtenstein">Liechtenstein</option>
        <option value="Lithuania">Lithuania</option>
        <option value="Luxembourg">Luxembourg</option>
        <option value="Macao">Macao</option>
        <option value="Macedonia">Macedonia</option>
        <option value="Madagascar">Madagascar</option>
        <option value="Malawi">Malawi</option>
        <option value="Malaysia">Malaysia</option>
        <option value="Maldives">Maldives</option>
        <option value="Mali">Mali</option>
        <option value="Malta">Malta</option>
        <option value="Marshall Islands">Marshall Islands</option>
        <option value="Martinique">Martinique</option>
        <option value="Mauritania">Mauritania</option>
        <option value="Mauritius">Mauritius</option>
        <option value="Mayotte">Mayotte</option>
        <option value="Mexico">Mexico</option>
        <option value="Micronesia">Micronesia</option>
        <option value="Moldova">Moldova</option>
        <option value="Monaco">Monaco</option>
        <option value="Mongolia">Mongolia</option>
        <option value="Montenegro">Montenegro</option>
        <option value="Montserrat">Montserrat</option>
        <option value="Morocco">Morocco</option>
        <option value="Mozambique">Mozambique</option>
        <option value="Myanmar">Myanmar</option>
        <option value="Namibia">Namibia</option>
        <option value="Nauru">Nauru</option>
        <option value="Nepal">Nepal</option>
        <option value="Netherlands">Netherlands</option>
        <option value="Netherlands Antilles">Netherlands Antilles</option>
        <option value="New Caledonia">New Caledonia</option>
        <option value="New Zealand">New Zealand</option>
        <option value="Nicaragua">Nicaragua</option>
        <option value="Niger">Niger</option>
        <option value="Nigeria">Nigeria</option>
        <option value="Niue">Niue</option>
        <option value="Norfolk Island">Norfolk Island</option>
        <option value="North Korea">North Korea</option>
        <option value="Northern Mariana Islands">Northern Mariana Islands</option>
        <option value="Norway">Norway</option>
        <option value="Oman">Oman</option>
        <option value="Pakistan">Pakistan</option>
        <option value="Palau">Palau</option>
        <option value="Palestinian Territory">Palestinian Territory</option>
        <option value="Panama">Panama</option>
        <option value="Papua New Guinea">Papua New Guinea</option>
        <option value="Paraguay">Paraguay</option>
        <option value="Peru">Peru</option>
        <option value="Philippines">Philippines</option>
        <option value="Pitcairn">Pitcairn</option>
        <option value="Poland">Poland</option>
        <option value="Portugal">Portugal</option>
        <option value="Puerto Rico">Puerto Rico</option>
        <option value="Qatar">Qatar</option>
        <option value="Republic of the Congo">Republic of the Congo</option>
        <option value="Reunion">Reunion</option>
        <option value="Romania">Romania</option>
        <option value="Russia">Russia</option>
        <option value="Rwanda">Rwanda</option>
        <option value="Saint Barthélemy">Saint Barthélemy</option>
        <option value="Saint Helena">Saint Helena</option>
        <option value="Saint Kitts and Nevis">Saint Kitts and Nevis</option>
        <option value="Saint Lucia">Saint Lucia</option>
        <option value="Saint Martin">Saint Martin</option>
        <option value="Saint Pierre and Miquelon">Saint Pierre and Miquelon</option>
        <option value="Saint Vincent and the Grenadines">Saint Vincent and the Grenadines</option>
        <option value="Samoa">Samoa</option>
        <option value="San Marino">San Marino</option>
        <option value="Sao Tome and Principe">Sao Tome and Principe</option>
        <option value="Saudi Arabia">Saudi Arabia</option>
        <option value="Senegal">Senegal</option>
        <option value="Serbia">Serbia</option>
        <option value="Serbia and Montenegro">Serbia and Montenegro</option>
        <option value="Seychelles">Seychelles</option>
        <option value="Sierra Leone">Sierra Leone</option>
        <option value="Singapore">Singapore</option>
        <option value="Slovakia">Slovakia</option>
        <option value="Slovenia">Slovenia</option>
        <option value="Solomon Islands">Solomon Islands</option>
        <option value="Somalia">Somalia</option>
        <option value="South Africa">South Africa</option>
        <option value="South Georgia and the South Sandwich Islands">South Georgia and the South Sandwich Islands</option>
        <option value="South Korea">South Korea</option>
        <option value="Spain">Spain</option>
        <option value="Sri Lanka">Sri Lanka</option>
        <option value="Sudan">Sudan</option>
        <option value="Suriname">Suriname</option>
        <option value="Svalbard and Jan Mayen">Svalbard and Jan Mayen</option>
        <option value="Swaziland">Swaziland</option>
        <option value="Sweden">Sweden</option>
        <option value="Switzerland">Switzerland</option>
        <option value="Syria">Syria</option>
        <option value="Taiwan">Taiwan</option>
        <option value="Tajikistan">Tajikistan</option>
        <option value="Tanzania">Tanzania</option>
        <option value="Thailand">Thailand</option>
        <option value="Togo">Togo</option>
        <option value="Tokelau">Tokelau</option>
        <option value="Tonga">Tonga</option>
        <option value="Trinidad and Tobago">Trinidad and Tobago</option>
        <option value="Tunisia">Tunisia</option>
        <option value="Turkey">Turkey</option>
        <option value="Turkmenistan">Turkmenistan</option>
        <option value="Turks and Caicos Islands">Turks and Caicos Islands</option>
        <option value="Tuvalu">Tuvalu</option>
        <option value="U.S. Virgin Islands">U.S. Virgin Islands</option>
        <option value="Uganda">Uganda</option>
        <option value="Ukraine">Ukraine</option>
        <option value="United Arab Emirates">United Arab Emirates</option>
        <option value="United Kingdom">United Kingdom</option>
        <option value="United States">United States</option>
        <option value="United States Minor Outlying Islands">United States Minor Outlying Islands</option>
        <option value="Uruguay">Uruguay</option>
        <option value="Uzbekistan">Uzbekistan</option>
        <option value="Vanuatu">Vanuatu</option>
        <option value="Vatican" data-iso="VA">Vatican</option>
        <option value="Venezuela" data-iso="VE">Venezuela</option>
        <option value="Vietnam" data-iso="VN">Vietnam</option>
        <option value="Wallis and Futuna" data-iso="WF">Wallis and Futuna</option>
        <option value="Western Sahara" data-iso="EH">Western Sahara</option>
        <option value="Yemen" data-iso="YE">Yemen</option>
        <option value="Zambia" data-iso="ZM">Zambia</option>
        <option value="Zimbabwe" data-iso="ZW">Zimbabwe</option>
        </select>
      <label>City</label>
      <input maxLength='50' class="input" type="text" name="city" placeholder="city..." />
      <label>Postal Code</label>
      <input maxLength='20' class="input" type="text" name="postal_code" placeholder="postal code..." />
      <label>Job Sector*</label>
      <input maxLength='100' class="input" type="text" required name="position_title" placeholder="job sector..." />
      
      <div className="position-container">
        <h3>Type of Position</h3>
        <label>
          <input
            type="radio"
            value="part-time"
            checked={selectedPosition === 'part-time'}
            onChange={handlePositionChange}
            name="position_type"
          />
          Part Time
        </label>
        <label>
          <input
            type="radio"
            value="full-time"
            checked={selectedPosition === 'full-time'}
            onChange={handlePositionChange}
            name="position_type"
          />
          Full Time
        </label>
      </div>

      <div className="position-container">
        <h3>Expected Duration</h3>
        <label>
          <input
            type="radio"
            value="permanent"
            checked={selectedDuration === 'permanent'}
            onChange={handleDurationChange}
            name="duration"
          />
          Permanent
        </label>
        <label>
          <input
            type="radio"
            value="temporary"
            checked={selectedDuration === 'temporary'}
            onChange={handleDurationChange}
            name="duration"
          />
          Temporary
        </label>
      </div>

      <label for="work_authorization">Work Authorization</label>
                  <select name="work_authorization" >
                  <option value="">Select</option>
<option value="1">H1-B</option>
<option value="2">L1-B</option>
<option value="3">L1-A</option>
<option value="4">L2-EAD</option>
<option value="5">B1</option>
<option value="6">Canadian Citizen</option>
<option value="7">GC</option>
<option value="8">GC-EAD</option>
<option value="9">OPT-EAD</option>
<option value="10">TN Visa</option>
<option value="11">Permanent Resident</option>
<option value="12">Open Work Permit</option>
<option value="13">Canada Authorized</option>
<option value="14">Green Card Holder</option>
<option value="15">US Authorized</option>
<option value="16">US Citizen</option>
<option value="17">Sponsorship Required</option></select>

<label className='addedstyling43'>Paste Resume*</label>
<Editor
required
  apiKey="lmrj7y4iu99lonaq3k8ewed6j7ksyxn3vreja1rk2cectzc4"
  name="resume"
  value={resume}
  init={{
    className: 'addedstyling47',
    width: '30%',
    menubar: false,
    plugins: [
      'advlist autolink lists link image charmap print preview anchor',
      'searchreplace visualblocks code fullscreen',
      'insertdatetime media table paste code help wordcount'
    ],
    toolbar: 'undo redo | formatselect | bold italic backcolor underline strikethrough |  link image media table mergetags | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent checklist | emoticons charmap typography | removeformat'
  }}

  
  onEditorChange={handleResumeChange}
/>
<textarea name="resume1" style={{display: 'none'}} value={resume} onChange={handleResumeChange} />

<label className='addedstyling43'>Anything you would like us to know?</label>
      <textarea
        name="message"
        placeholder="enter message here..."
        maxLength="500"
        value={message}
        onChange={handleMessageChange}
        style={{height: '145px'}}
      />
      <p className='addedstyling45'>{charCount}/500 characters</p>
      <input type="submit" value="Send" className="SeekerResume-send-button" />
    </form>
  );
}

export default ContactForm;
