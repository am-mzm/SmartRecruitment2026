import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Nav from './components/Nav';
import Page1 from './components/Home';
import Footer from './components/Footer';
import {createRoot} from 'react-dom/client';
import Page2 from './components/About';
import AboutInfo from './components/AboutInfo';
import JobSeekers from './components/JobSeekers';
import Employers from './components/Employers';
import Contact from './components/Contact';
import AboutValues from './components/AboutValues';
import SeekerResume from './components/JobSeekersResume';
import YourComponent from './components/JobSeekersSearchJobs';
import HireTalent from './components/EmployersHireTalent';
import GeneralRequests from './components/ContactGeneralRequests'; 
import AboutOfficeLocations from './components/AboutOfficeLocations';
import SeekersWorkForUs from './components/JobSeekersWorkForUs';
import AboutLogin from './components/AboutLogin.tsx';
import App from './components/Smart-Recruitment/App.tsx';
import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { msalConfig } from "./components/authConfigur.ts";
// import { msalConfig } from './components/authConfigur';
import ProtectedRoute from './components/Smart-Recruitment/ProtectedRoute.tsx';
// import Modal from 'react-modal';

const msalInstance = new PublicClientApplication(msalConfig)

// Modal.setAppElement("#root");

const rootElement = 
document.getElementById('root');
const root = 
createRoot(rootElement);
root.render(
  <MsalProvider instance={msalInstance}>
  {/* The block of code above was added */}
  <BrowserRouter>
  <Routes>
      <Route path="/AboutUs/OurValues" element={<>
      <Nav /> 
      <AboutValues />
      <Footer />
      </>} />
  
      <Route path="/AboutUs/WhoWeAre" element={<>
      <Nav /> 
      <AboutInfo />
      <Footer />
      </>} />

      <Route path="/AboutUs/OfficeLocations" element={<>
      <Nav /> 
      <AboutOfficeLocations />
      <Footer />
      </>} />

      {/* This block of code was added */}
      <Route path="/AboutUs/Login" element={<> {/* Added for the login page */}
      <Nav />
      <AboutLogin />
      <Footer />
      </>} />
      
      {/* This block of code was added */}
      <Route path="/AboutUs/Login/Smart-Recruitment" element={ 
      <ProtectedRoute element={<>
      <Nav />
      <App />
      <Footer />
      </>} /> } />
  
      <Route path="/AboutUs" element={<>
      <Nav /> 
      <Page2 />
      <Footer />
      </>} />
  
      <Route path="/JobSeekers" element={<>
      <Nav /> 
      <JobSeekers />
      <Footer />
      </>} />
  
      <Route path="/Employers" element={<>
      <Nav /> 
      <Employers />
      <Footer />
      </>} />

      <Route path="/Employers/HireTalent" element={<>
      <Nav /> 
      <HireTalent />
      <Footer />
      </>} />
  
      <Route path="/ContactUs" element={<>
      <Nav /> 
      <Contact />
      <Footer />
      </>} />
  
      <Route path="/" element={<>
      <Nav /> 
      <Page1 />
      <Footer />
      </>} />

      <Route path="/JobSeekers/SendResume" element={<>
      <Nav /> 
      <SeekerResume />
      <Footer />
      </>} />

      <Route path="/JobSeekers/SearchJobs" element={<>
      <Nav/> 
      <div style={{display: 'none'}}class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
         <div class="nav-text">
            <p onClick={() => window.location.href = "/"}  class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers"}  class="Page1-descr"> Job Seekers</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers/SearchJobs"}  class="Page1-descr"> Search Jobs</p>
            </div>
      <YourComponent />
      <Footer />
      </>} />

      <Route path="/ContactUs/GeneralRequests" element={<>
      <Nav /> 
      <GeneralRequests />
      <Footer />
      </>} />

      <Route path="/JobSeekers/WorkForUs" element={<>
      <Nav /> 
      <SeekersWorkForUs />
      <Footer />
      </>} />
     
  </Routes>
  </BrowserRouter>,
  
  {/* Added for entraID authentication */}
  </MsalProvider>
);
