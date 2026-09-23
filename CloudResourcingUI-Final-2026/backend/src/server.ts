import { prisma } from "./client";
import express, { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import jwksRsa from 'jwks-rsa';
import cors from 'cors';
// import ip from 'ip'
import session from 'express-session'
import 'dotenv/config'
import geoip from 'geoip-lite';
import axios from 'axios';

const app = express(); // Instantiate Express
const router = express.Router();
const port = process.env.PORT || 3001; // Define port that the backend server will run on

interface Authentication extends Request{
    user?: any;
}

const sessionSecret = process.env.REACT_APP_SESSION_SECRET;
if (!sessionSecret) {
    throw new Error('SESSION_SECRET is not defined');
}

app.use(cors()); // Enable CORS which will act as a middleware(allowing the frontend to make requests to the backend)

app.use(express.json()); // Enable JSON parsing for incoming requests

app.use(session({
    secret: sessionSecret, 
    resave: false, 
    saveUninitialized: true, 
    cookie: { secure: false } 
}));

// const getClientIp = (req: Request, res: Response, next: NextFunction) => {
//     let ipAddress = Array.isArray(req.headers['x-forwarded-for']) 
//         ? req.headers['x-forwarded-for'][0] 
//         : req.headers['x-forwarded-for']?.split(',').shift() || req.socket.remoteAddress;

//     // Check if the IP address is IPv6 and convert to IPv4 if necessary
//     if (ipAddress && ipAddress.includes('::ffff:')) {
//         ipAddress = ipAddress.split('::ffff:')[1];
//     }

//     // Ensure the IP address is in IPv4 format
//     if (ipAddress && ipAddress.includes(':')) {
//         ipAddress = ip.address(); // Use the ip library to get the server's IP address
//     }

//     req.clientIp = ipAddress ?? undefined;
//     next();
// };

// app.use(getClientIp);

const getPublicIp = async (): Promise<string> => {
    try {
        console.log('Fetching public IP address...');
        const response = await axios.get('https://api.ipify.org?format=json');
        console.log('Response from IP address service:', response.data);
        return response.data.ip;
    } catch (error) {
        console.error('Error fetching public IP address:', error);
        return 'unknown';
    }
};

// const getPrivateIp = (req: Request): string => {
//     let ipAddress = Array.isArray(req.headers['x-forwarded-for']) 
//         ? req.headers['x-forwarded-for'][0] 
//         : req.headers['x-forwarded-for']?.split(',').shift() || req.socket.remoteAddress;
    
//     console.log('Headers:', req.headers);
//     console.log('Remote Address:', req.socket.remoteAddress);

//     // Check if the IP address is IPv6 and convert to IPv4 if necessary
//     if (ipAddress && ipAddress.includes('::ffff:')) {
//         ipAddress = ipAddress.split('::ffff:')[1];
//     }

//     // Ensure the IP address is in IPv4 format
//     if (ipAddress && ipAddress.includes(':')) {
//         ipAddress = ip.address(); // Use the ip library to get the server's IP address
//     }

//     return ipAddress ?? 'unknown';
// };

// app.use(requestIp.mw());
// app.use(getClientIp);

const authenticateToken = (req: Authentication, res:Response, next: NextFunction): void => {
    const headerAuth = req.headers['authentication']
    const token  = typeof headerAuth === 'string' ? headerAuth.split(' ')[1] : null; // Extract the token from the header, for example("Bearer a1b2c3") and we take a1b2c3
    // console.log('Token:', token);

    if(token == null){
        res.sendStatus(401)
        return;
    }

    const client = jwksRsa({
        jwksUri: `${process.env.REACT_APP_AUTHORITY}/discovery/v2.0/keys`
    });
    const getKey = (header: any, callback: any) => {
        // console.log('JWT Header:', header);
        client.getSigningKey(header.kid, function(err: any, key: any) {
            if (err) {
                console.error('Error getting signing key:', err);
                return callback(err);
            }
            if (!key) {
                console.error('Signing key not found');
                return callback(new Error('Signing key not found'));
            }
            const signingKey = key.getPublicKey();
            callback(null, signingKey);
        });
    }
    

    jwt.verify(token, getKey, {}, (err, user) => {
        if (err){
            console.error('Error verifying token:', err);
            return res.sendStatus(403)
        }
        req.user = user;
        next()
    }); 
}

router.use(authenticateToken);


app.get('/api', authenticateToken, (req, res) => {
    res.json({ message: 'Welcome to the API!' });
});

// Define a route to fetch all boolean pairs
router.get('/booleanPairs', async (req: Request, res: Response) => { // 
    try {
        const booleanPairs = await prisma.bOOLEANNAMEVALUEPAIR.findMany({ // Fetch all boolean pairs from the database table "BOOLEANNAMEVALUEPAIR"
        select: {
            BOOLEANNAMEVALUEPAIRID: true,
            BOOLEANNAME: true,
            BOOLEANVALUE: true
        }
        });
        // console.log(booleanPairs);
        res.json(booleanPairs); // Send the boolean pairs as a response
    } catch (error) {
        console.error("Error fetching boolean pairs", error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.put('/booleanPairs/:id', async (req: Request, res: Response) => {
    const {id} = req.params;
    const {BOOLEANNAME, BOOLEANVALUE} = req.body;

    try {
        const updatedBooleanPair = await prisma.bOOLEANNAMEVALUEPAIR.update({
            where: {BOOLEANNAMEVALUEPAIRID: parseInt(id)},
            data: {
                BOOLEANNAME,
                BOOLEANVALUE,
                UPDATEDDATE: new Date(),
                UPDATEDBY: 'Admin'   
            }
        });
        res.json(updatedBooleanPair);
    } catch (error) {   
        console.error("Error updating boolean pair", error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.post('/booleanPairs', async (req: Request, res: Response) => {
    const {BOOLEANNAMEVALUEPAIRID, BOOLEANNAME, BOOLEANVALUE} = req.body;
    
    try{
        const newBooleanPair = await prisma.bOOLEANNAMEVALUEPAIR.create({
            data: {
                BOOLEANNAME,
                BOOLEANVALUE,
                CREATEDDATE: new Date(),
                CREATEDBY: 'system'
            }
        });
        res.status(201).json(newBooleanPair);
    } catch (error) {
        console.error("Error creating boolean pair", error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.delete('/booleanPairs/:id', async (req: Request, res: Response) =>{
    const { id } = req.params;

    try{
        await prisma.bOOLEANNAMEVALUEPAIR.delete({
            where: {BOOLEANNAMEVALUEPAIRID: parseInt(id)},
        });
        res.status(204).send();
    } catch (error) {
        console.error("Error deleting boolean pair", error);
        res.status(500).json({error: "Internal Server Error"})
    }
});

router.get('/booleanSearchHistory', async (req: Request, res: Response): Promise<void> => {
    const { jobTitle } = req.query;

    console.log('Received request to fetch boolean search history');
    console.log('Job Title:', jobTitle);

    if (!jobTitle) {
        console.log('Job title is required');
        res.status(400).json({ error: 'Job title is required' });
        return;
    }

    try {
        const booleanHistory = await prisma.bOOLEANNAMEVALUESEARCHHISTORY.findMany({
            where: {
                JOBTITLE: {
                    startsWith: jobTitle as string,
                }
            },
            orderBy: {
                BOOLEANNAMEVALUESEARCHHISTORYID: 'desc'
            },
            take: 10,
            include: {
                BOOLEANHISTORYNAMESEARCHMAP: {
                    include: {
                        BOOLEANNAMEVALUEPAIR: true
                    }
                }
            }
        });

        console.log('Boolean history fetched:', booleanHistory);

        if (booleanHistory.length === 0) {
            console.log('No records found for the given job title');
            res.status(404).json({ error: 'No records found for the given job title' });
            return;
        }

        const result = booleanHistory.map((history: any) => ({
            jobTitle: history.JOBTITLE,
            jobDescription: history.JOBDESCRIPTION,
            booleanPhrase: history.BOOLEANPHRASE,
            technologyRequirements: history.BOOLEANHISTORYNAMESEARCHMAP.map((map: { BOOLEANNAMEVALUEPAIR: { BOOLEANNAMEVALUEPAIRID: number; BOOLEANNAME: string; BOOLEANVALUE: boolean; };}) => ({
                BOOLEANNAMEVALUEPAIRID: map.BOOLEANNAMEVALUEPAIR.BOOLEANNAMEVALUEPAIRID,
                BOOLEANNAME: map.BOOLEANNAMEVALUEPAIR.BOOLEANNAME,
                BOOLEANVALUE: map.BOOLEANNAMEVALUEPAIR.BOOLEANVALUE
                // BOOLEANNAMEVALUEPAIRWEIGHTAGE: map.BOOLEANNAMEVALUEPAIRWEIGHTAGE
            }))
        }));
        
        console.log('Result:', result);
        res.json(result);
    } catch (error) {
        console.error("Error fetching boolean search history", error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.post('/booleanSearchHistory', async (req: Request, res: Response) => {
    const {jobTitle, jobDescription, booleanPhrase, technologyRequirements} = req.body;
    
    // console.log('Received request to save boolean search history');
    // console.log('Job Title:', jobTitle);
    // console.log('Job Description:', jobDescription);
    // console.log('Boolean Phrase:', booleanPhrase);
    // console.log('Technology Requirements:', technologyRequirements);

    try{
        const newBooleanHistory = await prisma.bOOLEANNAMEVALUESEARCHHISTORY.create({
            data: {
                JOBTITLE: jobTitle,
                JOBDESCRIPTION: jobDescription,
                BOOLEANPHRASE: booleanPhrase,
                CREATEDDATE: new Date(),
                CREATEDBY: 'system',
                BOOLEANHISTORYNAMESEARCHMAP: {
                    create: technologyRequirements.map((req: {BOOLEANNAMEVALUEPAIRID: number, weightage: number}) => ({
                        BOOLEANNAMEVALUEPAIRID: req.BOOLEANNAMEVALUEPAIRID,
                        BOOLEANNAMEVALUEPAIRWEIGHTAGE: null
                    }))
                }
            },
            include: {
                BOOLEANHISTORYNAMESEARCHMAP: true
            }
        });
        // console.log('New boolean history saved:', newBooleanHistory);
        res.status(201).json(newBooleanHistory);
    } catch (error) {
        console.error("Error saving boolean histor", error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.get('/recentBooleanSearchHistory', async (req: Request, res: Response): Promise<void> => {
    console.log('Received request to fetch the three most recent boolean search history records');
  
    try {
      const recentBooleanHistory = await prisma.bOOLEANNAMEVALUESEARCHHISTORY.findMany({
        orderBy: {
          BOOLEANNAMEVALUESEARCHHISTORYID: 'desc'
        },
        take: 3,
        include: {
          BOOLEANHISTORYNAMESEARCHMAP: {
            include: {
              BOOLEANNAMEVALUEPAIR: true
            }
          }
        }
      });
  
    //   console.log('Recent boolean history fetched:', recentBooleanHistory);
  
      if (recentBooleanHistory.length === 0) {
        console.log('No records found');
        res.status(404).json({ error: 'No records found' });
        return;
      }
  
      const result = recentBooleanHistory.map(history => ({
        jobTitle: history.JOBTITLE,
        jobDescription: history.JOBDESCRIPTION,
        booleanPhrase: history.BOOLEANPHRASE,
        technologyRequirements: history.BOOLEANHISTORYNAMESEARCHMAP.map(map => ({
            BOOLEANNAMEVALUEPAIRID: map.BOOLEANNAMEVALUEPAIR.BOOLEANNAMEVALUEPAIRID,
            BOOLEANNAME: map.BOOLEANNAMEVALUEPAIR.BOOLEANNAME,
            BOOLEANVALUE: map.BOOLEANNAMEVALUEPAIR.BOOLEANVALUE,
            // BOOLEANNAMEVALUEPAIRWEIGHTAGE: map.BOOLEANNAMEVALUEPAIRWEIGHTAGE
        }))
      }));
  
    //   console.log('Result:', result);
      res.json(result);
    } catch (error) {
      console.error("Error fetching recent boolean search history", error);
      res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.post('/userInfo', async (req: Request, res: Response): Promise<void> => {
    const { sub, username, email} = req.body;
    // const privateIpAddress = getPrivateIp(req);
    const publicIpAddress = await getPublicIp();
    // const publicIpAddress = null;

    console.log(`Public IP Address: ${publicIpAddress}`)

    // console.log(`User Info: ${username}, Email: ${email}, IP Address: ${ipAddress}, Sub: ${sub}`);

    // Log the user information
    console.log(`User Information:
        USERGRID: ${sub}
        USERNAME: ${username}
        EMAIL: ${email}
    `);

    try {
        const existingUser = await prisma.uSERINFO.findFirst({
            where: { USERGRID: sub }
        });

        let userInfo;
        if (existingUser) {
            console.log('User already exists:', existingUser);
            userInfo = existingUser;
        } else {
            userInfo = await prisma.uSERINFO.create({
                data: {
                    USERGRID: sub,
                    USERNAME: username,
                    EMAIL: email,
                    CREATEDDATE: new Date(),
                    CREATEDBY: 'system'
                }
            });
            console.log('New user created:', userInfo);
        }

        const existingSession = await prisma.uSERSESSIONDETAILS.findFirst({
            where: {
                USERINFOID: userInfo.USERINFOID,
                LOGGEDOUTTIME: null
            }
        });

        let sessionId;
        let newSession;

        if (existingSession) {
            console.log('Existing active session found:', existingSession);
            sessionId = existingSession.SESSIONID;
            newSession = existingSession;

        } else {
            sessionId = req.sessionID;

            const geo = geoip.lookup(publicIpAddress || 'unknown');
            const location = geo?.city || 'unknown';
            const country = geo?.country || 'unknown'

            console.log(`Found Location: ${location} and Found Country: ${country}`)

            newSession = await prisma.uSERSESSIONDETAILS.create({
                data: {
                    SESSIONID: sessionId,
                    USERINFOID: userInfo.USERINFOID,
                    IPADDRESS: publicIpAddress || 'unknown',
                    LOCATION: location,
                    COUNTRY: country, 
                    LOGGEDINTIME: new Date(),
                    LOGGEDOUTTIME: null
                }
            });
            console.log('New session created:', newSession);
        }

        res.json({ message: 'User info and session details logged and stored.', userInfo, newSession });
    } catch (error) {
        console.error('Error storing user info or session details:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.put('/userSessionLogout', async(req: Request, res: Response): Promise<void> => {
    const {sessionId} = req.body;

    if (!sessionId) {
        console.error('Session ID is missing');
        res.status(400).json({ error: 'Session ID is required' });
        return;
    }

    try{
        const updatedSession = await prisma.uSERSESSIONDETAILS.updateMany({
            where: {SESSIONID: sessionId},
            data: {LOGGEDOUTTIME: new Date()}
        })

        if(updatedSession.count === 0){
            console.log('Session not found for sessionId:', sessionId);
            res.status(404).json({error: 'Session not found'});
            return;
        }

        console.log('Logout time updated for sessionId:', sessionId);
        res.json({message: 'Logout time updated successfully'})
    } catch(error){
        console.error('Error updating logout time', error);
        res.status(500).json({error: 'Internal Server Error'});
    }
})

// router.post('/userLoginInfo', async(req: Request, res: Response) => {
//     // const ipAddress = Array.isArray(req.headers['x-forwarded-for']) ? req.headers['x-forwarded-for'][0] : req.headers['x-forwarded-for']?.split(',').shift() || req.socket.remoteAddress;

//     const { username, email, machineName, sub, status } = req.body;
//     const ipAddress = req.clientIp;

//     console.log(`User ${status}: ${username}, Email: ${email}, IP Address: ${ipAddress}, Machine Name: ${machineName}, Sub: ${sub}`);

//     // Log the user information
//     console.log(`User Information:
//         Username: ${username}
//         Email: ${email}
//         IP Address: ${ipAddress}
//         Machine Name: ${machineName}
//         Sub: ${sub}
//         Status: ${status}
//     `);

//     res.json({ message: 'User info logged.' });
// });

app.use('/api', router);

// Prints in terminal which port the server is running on
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
