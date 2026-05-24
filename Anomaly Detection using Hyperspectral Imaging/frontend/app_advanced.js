// Advanced JavaScript Application
// Features: WebSocket, Charts, Dark Mode, Authentication, Advanced Animations

const API_BASE_URL = 'http://127.0.0.1:8000';
let authToken = null;
let currentUser = null;
let ws = null;
let scoreChart = null;
let comparisonChart = null;
let currentImageView = 'rgb';
let detectionHistory = [];
let totalDetections = 0;
let totalProcessingTime = 0;
let detectionMap = null;
let detectionMarker = null;

// Indian States and Cities to Coordinates Mapping
const locationCoordinates = {
    // Indian States (with approximate center coordinates)
    'Andhra Pradesh': { lat: 15.9129, lon: 79.7400 },
    'Arunachal Pradesh': { lat: 28.2180, lon: 94.7278 },
    'Assam': { lat: 26.2006, lon: 92.9376 },
    'Bihar': { lat: 25.0961, lon: 85.3131 },
    'Chhattisgarh': { lat: 21.2787, lon: 81.8661 },
    'Goa': { lat: 15.2993, lon: 74.1240 },
    'Gujarat': { lat: 22.2587, lon: 71.1924 },
    'Haryana': { lat: 29.0588, lon: 76.0856 },
    'Himachal Pradesh': { lat: 31.1048, lon: 77.1734 },
    'Jharkhand': { lat: 23.6102, lon: 85.2799 },
    'Karnataka': { lat: 15.3173, lon: 75.7139 },
    'Kerala': { lat: 10.8505, lon: 76.2711 },
    'Madhya Pradesh': { lat: 22.9734, lon: 78.6569 },
    'Maharashtra': { lat: 19.7515, lon: 75.7139 },
    'Manipur': { lat: 24.6637, lon: 93.9063 },
    'Meghalaya': { lat: 25.4670, lon: 91.3662 },
    'Mizoram': { lat: 23.1645, lon: 92.9376 },
    'Nagaland': { lat: 26.1584, lon: 94.5624 },
    'Odisha': { lat: 20.9517, lon: 85.0985 },
    'Punjab': { lat: 31.1471, lon: 75.3412 },
    'Rajasthan': { lat: 27.0238, lon: 74.2179 },
    'Sikkim': { lat: 27.5330, lon: 88.6139 },
    'Tamil Nadu': { lat: 11.1271, lon: 78.6569 },
    'Telangana': { lat: 18.1124, lon: 79.0193 },
    'Tripura': { lat: 23.7451, lon: 91.7462 },
    'Uttar Pradesh': { lat: 26.8467, lon: 80.9462 },
    'Uttarakhand': { lat: 30.0668, lon: 79.0193 },
    'West Bengal': { lat: 22.9868, lon: 87.8550 },
    'Jammu and Kashmir': { lat: 33.7782, lon: 76.5762 },
    'Delhi': { lat: 28.7041, lon: 77.1025 },
    'Puducherry': { lat: 11.9416, lon: 79.8083 },
    'Chandigarh': { lat: 30.7333, lon: 76.7794 },
    'Ladakh': { lat: 34.1526, lon: 77.5770 },
    
    // Major Indian Cities with State Names
    'Mumbai, Maharashtra': { lat: 19.0760, lon: 72.8777 },
    'Delhi, Delhi': { lat: 28.7041, lon: 77.1025 },
    'Bangalore, Karnataka': { lat: 12.9716, lon: 77.5946 },
    'Hyderabad, Telangana': { lat: 17.3850, lon: 78.4867 },
    'Chennai, Tamil Nadu': { lat: 13.0827, lon: 80.2707 },
    'Kolkata, West Bengal': { lat: 22.5726, lon: 88.3639 },
    'Pune, Maharashtra': { lat: 18.5204, lon: 73.8567 },
    'Ahmedabad, Gujarat': { lat: 23.0225, lon: 72.5714 },
    'Jaipur, Rajasthan': { lat: 26.9124, lon: 75.7873 },
    'Lucknow, Uttar Pradesh': { lat: 26.8467, lon: 80.9462 },
    'Kanpur, Uttar Pradesh': { lat: 26.4499, lon: 80.3319 },
    'Nagpur, Maharashtra': { lat: 21.1458, lon: 79.0882 },
    'Indore, Madhya Pradesh': { lat: 22.7196, lon: 75.8577 },
    'Thane, Maharashtra': { lat: 19.2183, lon: 72.9781 },
    'Bhopal, Madhya Pradesh': { lat: 23.2599, lon: 77.4126 },
    'Visakhapatnam, Andhra Pradesh': { lat: 17.6868, lon: 83.2185 },
    'Pimpri-Chinchwad, Maharashtra': { lat: 18.6298, lon: 73.7997 },
    'Patna, Bihar': { lat: 25.5941, lon: 85.1376 },
    'Vadodara, Gujarat': { lat: 22.3107, lon: 73.1926 },
    'Ghaziabad, Uttar Pradesh': { lat: 28.6692, lon: 77.4538 },
    'Ludhiana, Punjab': { lat: 30.9010, lon: 75.8573 },
    'Agra, Uttar Pradesh': { lat: 27.1751, lon: 78.0421 },
    'Nashik, Maharashtra': { lat: 19.9975, lon: 73.7898 },
    'Ranchi, Jharkhand': { lat: 23.3441, lon: 85.3096 },
    'Faridabad, Haryana': { lat: 28.4089, lon: 77.3178 },
    'Meerut, Uttar Pradesh': { lat: 28.9844, lon: 77.7064 },
    'Rajkot, Gujarat': { lat: 22.2736, lon: 70.8012 },
    'Varanasi, Uttar Pradesh': { lat: 25.3176, lon: 82.9739 },
    'Srinagar, Jammu and Kashmir': { lat: 34.0837, lon: 74.7973 },
    'Aurangabad, Maharashtra': { lat: 19.8762, lon: 75.3433 },
    'Dhanbad, Jharkhand': { lat: 23.7957, lon: 86.4304 },
    'Amritsar, Punjab': { lat: 31.6340, lon: 74.8723 },
    'Navi Mumbai, Maharashtra': { lat: 19.0330, lon: 73.0297 },
    'Allahabad, Uttar Pradesh': { lat: 25.4358, lon: 81.8463 },
    'Howrah, West Bengal': { lat: 22.5958, lon: 88.2636 },
    'Jabalpur, Madhya Pradesh': { lat: 23.1815, lon: 79.9864 },
    'Gwalior, Madhya Pradesh': { lat: 26.2124, lon: 78.1772 },
    'Vijayawada, Andhra Pradesh': { lat: 16.5062, lon: 80.6480 },
    'Jodhpur, Rajasthan': { lat: 26.2389, lon: 73.0243 },
    'Madurai, Tamil Nadu': { lat: 9.9252, lon: 78.1198 },
    'Raipur, Chhattisgarh': { lat: 21.2514, lon: 81.6296 },
    'Kota, Rajasthan': { lat: 25.1381, lon: 75.8344 },
    'Guwahati, Assam': { lat: 26.1445, lon: 91.7362 },
    'Chandigarh, Chandigarh': { lat: 30.7333, lon: 76.7794 },
    'Solapur, Maharashtra': { lat: 17.6599, lon: 75.9064 },
    'Hubli-Dharwad, Karnataka': { lat: 15.3647, lon: 75.1240 },
    'Bareilly, Uttar Pradesh': { lat: 28.3670, lon: 79.4304 },
    'Moradabad, Uttar Pradesh': { lat: 28.8386, lon: 78.7733 },
    'Mysore, Karnataka': { lat: 12.2958, lon: 76.6394 },
    'Gurgaon, Haryana': { lat: 28.4595, lon: 77.0266 },
    'Aligarh, Uttar Pradesh': { lat: 27.8801, lon: 78.0798 },
    'Jalandhar, Punjab': { lat: 31.3260, lon: 75.5762 },
    'Tiruchirappalli, Tamil Nadu': { lat: 10.7905, lon: 78.7047 },
    'Bhubaneswar, Odisha': { lat: 20.2961, lon: 85.8245 },
    'Salem, Tamil Nadu': { lat: 11.6643, lon: 78.1460 },
    'Mira-Bhayandar, Maharashtra': { lat: 19.2982, lon: 72.8495 },
    'Warangal, Telangana': { lat: 17.9689, lon: 79.5939 },
    'Thiruvananthapuram, Kerala': { lat: 8.5241, lon: 76.9366 },
    'Bhiwandi, Maharashtra': { lat: 19.2988, lon: 73.0600 },
    'Saharanpur, Uttar Pradesh': { lat: 29.9669, lon: 77.5463 },
    'Dehradun, Uttarakhand': { lat: 30.3165, lon: 78.0322 },
    'Asansol, West Bengal': { lat: 23.6738, lon: 86.9524 },
    'Nanded, Maharashtra': { lat: 19.1576, lon: 77.3128 },
    'Kochi, Kerala': { lat: 9.9312, lon: 76.2673 },
    'Coimbatore, Tamil Nadu': { lat: 11.0168, lon: 76.9558 },
    'Surat, Gujarat': { lat: 21.1702, lon: 72.8311 },
    'Mangalore, Karnataka': { lat: 12.9141, lon: 74.8560 },
    'Vellore, Tamil Nadu': { lat: 12.9165, lon: 79.1325 },
    'Bikaner, Rajasthan': { lat: 28.0229, lon: 73.1872 },
    'Cuttack, Odisha': { lat: 20.4625, lon: 85.8830 },
    'Firozabad, Uttar Pradesh': { lat: 27.1517, lon: 78.3936 },
    'Kochi, Kerala': { lat: 9.9312, lon: 76.2673 },
    'Nellore, Andhra Pradesh': { lat: 14.4429, lon: 79.9864 },
    'Bhavnagar, Gujarat': { lat: 21.7642, lon: 72.1519 },
    'Dehradun, Uttarakhand': { lat: 30.3165, lon: 78.0322 },
    'Durgapur, West Bengal': { lat: 23.5204, lon: 87.3119 },
    'Asansol, West Bengal': { lat: 23.6738, lon: 86.9524 },
    'Rourkela, Odisha': { lat: 22.2515, lon: 84.8663 },
    'Noida, Uttar Pradesh': { lat: 28.5355, lon: 77.3910 },
    'Siliguri, West Bengal': { lat: 26.7160, lon: 88.4270 },
    'Jammu, Jammu and Kashmir': { lat: 32.7266, lon: 74.8570 },
    'Udaipur, Rajasthan': { lat: 24.5854, lon: 73.7125 },
    'Bhilai, Chhattisgarh': { lat: 21.1956, lon: 81.3686 },
    'Alwar, Rajasthan': { lat: 27.5529, lon: 76.6345 },
    'Korba, Chhattisgarh': { lat: 22.3510, lon: 82.6896 },
    'Bhilwara, Rajasthan': { lat: 25.3515, lon: 74.6387 },
    'Berhampur, Odisha': { lat: 19.3045, lon: 84.7973 },
    'Muzaffarnagar, Uttar Pradesh': { lat: 29.4737, lon: 77.7087 },
    'Guntur, Andhra Pradesh': { lat: 16.3067, lon: 80.4365 },
    'Jhansi, Uttar Pradesh': { lat: 25.4333, lon: 78.5824 },
    'Sambalpur, Odisha': { lat: 21.4700, lon: 84.0200 },
    'Khanna, Punjab': { lat: 30.7412, lon: 76.2127 },
    'Allahabad, Uttar Pradesh': { lat: 25.4358, lon: 81.8463 },
    'Mangalore, Karnataka': { lat: 12.9141, lon: 74.8560 },
    'Ujjain, Madhya Pradesh': { lat: 23.1763, lon: 75.7885 },
    'Mathura, Uttar Pradesh': { lat: 27.4924, lon: 77.6999 },
    'Jalandhar, Punjab': { lat: 31.3260, lon: 75.5762 },
    'Bharatpur, Rajasthan': { lat: 27.2153, lon: 77.4920 },
    'Kollam, Kerala': { lat: 8.8804, lon: 76.5900 },
    'Ajmer, Rajasthan': { lat: 26.4499, lon: 74.6399 },
    'Tiruppur, Tamil Nadu': { lat: 11.1085, lon: 77.3417 },
    'Gulbarga, Karnataka': { lat: 17.3297, lon: 76.8343 },
    'Jamnagar, Gujarat': { lat: 22.4707, lon: 70.0577 },
    'Bhubaneswar, Odisha': { lat: 20.2961, lon: 85.8245 },
    'Dhule, Maharashtra': { lat: 20.8420, lon: 74.7733 },
    'Kozhikode, Kerala': { lat: 11.2588, lon: 75.7804 },
    'Akola, Maharashtra': { lat: 20.7002, lon: 77.0082 },
    'Rajkot, Gujarat': { lat: 22.2736, lon: 70.8012 },
    'Kota, Rajasthan': { lat: 25.1381, lon: 75.8344 },
    'Nanded, Maharashtra': { lat: 19.1576, lon: 77.3128 },
    'Amravati, Maharashtra': { lat: 20.9374, lon: 77.7796 },
    'Patiala, Punjab': { lat: 30.3398, lon: 76.3869 },
    'Bokaro, Jharkhand': { lat: 23.6738, lon: 86.1424 },
    'Agartala, Tripura': { lat: 23.8315, lon: 91.2868 },
    'Bhagalpur, Bihar': { lat: 25.2416, lon: 86.9755 },
    'Muzaffarpur, Bihar': { lat: 26.1226, lon: 85.3905 },
    'Latur, Maharashtra': { lat: 18.4087, lon: 76.5603 },
    'Davanagere, Karnataka': { lat: 14.4644, lon: 75.9280 },
    'Kozhikode, Kerala': { lat: 11.2588, lon: 75.7804 },
    'Amaravati, Maharashtra': { lat: 20.9374, lon: 77.7796 },
    'Vijayapura, Karnataka': { lat: 16.8302, lon: 75.7055 },
    'Kannur, Kerala': { lat: 11.8745, lon: 75.3704 },
    'Karimnagar, Telangana': { lat: 18.4376, lon: 79.1231 },
    'Tumkur, Karnataka': { lat: 13.3389, lon: 77.1166 },
    'Khammam, Telangana': { lat: 17.2473, lon: 80.1515 },
    'Ongole, Andhra Pradesh': { lat: 15.5055, lon: 80.0494 },
    'Deoghar, Jharkhand': { lat: 24.4895, lon: 86.7040 },
    'Chittoor, Andhra Pradesh': { lat: 13.2172, lon: 79.1285 },
    'Kurnool, Andhra Pradesh': { lat: 15.8281, lon: 78.0373 },
    'Udupi, Karnataka': { lat: 13.3409, lon: 74.7421 },
    'Rajahmundry, Andhra Pradesh': { lat: 17.0005, lon: 81.8068 },
    'Karawal Nagar, Delhi': { lat: 28.6479, lon: 77.2729 },
    'Srikakulam, Andhra Pradesh': { lat: 18.2975, lon: 83.8967 },
    'Nizamabad, Telangana': { lat: 18.6725, lon: 78.0946 },
    'Sagar, Madhya Pradesh': { lat: 23.8357, lon: 78.7428 },
    'Dibrugarh, Assam': { lat: 27.4728, lon: 94.9123 },
    'Imphal, Manipur': { lat: 24.8079, lon: 93.9440 },
    'Ranchi, Jharkhand': { lat: 23.3441, lon: 85.3096 },
    'Agartala, Tripura': { lat: 23.8315, lon: 91.2868 },
    'Kohima, Nagaland': { lat: 25.6701, lon: 94.1078 },
    'Aizawl, Mizoram': { lat: 23.7271, lon: 92.7176 },
    'Gangtok, Sikkim': { lat: 27.3314, lon: 88.6138 },
    'Itanagar, Arunachal Pradesh': { lat: 27.0844, lon: 93.6053 },
    'Leh, Ladakh': { lat: 34.1526, lon: 77.5770 },
    'Port Blair, Andaman and Nicobar': { lat: 11.6672, lon: 92.7612 },
    'Kolhapur': { lat: 16.7050, lon: 74.2433 },
    'Ajmer': { lat: 26.4499, lon: 74.6399 },
    'Akola': { lat: 20.7002, lon: 77.0082 },
    'Gulbarga': { lat: 17.3283, lon: 76.8345 },
    'Jamshedpur': { lat: 22.8046, lon: 86.2029 },
    'Bhilai': { lat: 21.2140, lon: 81.6427 },
    'Cuttack': { lat: 20.4625, lon: 85.8830 },
    'Firozabad': { lat: 27.1475, lon: 78.3948 },
    'Kochi': { lat: 9.9312, lon: 76.2673 },
    'Nellore': { lat: 14.4426, lon: 79.9865 },
    'Bhavnagar': { lat: 21.7643, lon: 72.1519 },
    'Durgapur': { lat: 23.5204, lon: 87.3119 },
    'Imphal': { lat: 24.8170, lon: 93.9360 },
    'Ratlam': { lat: 23.3298, lon: 75.0368 },
    'Hapur': { lat: 28.7284, lon: 77.7701 },
    'Arrah': { lat: 25.5602, lon: 84.6623 },
    'Anantapur': { lat: 14.6798, lon: 77.5989 },
    'Karimnagar': { lat: 18.4360, lon: 79.1528 },
    'Etawah': { lat: 26.7705, lon: 79.0114 },
    'Ambattur': { lat: 13.1015, lon: 80.1514 },
    'North Dumdum': { lat: 22.6062, lon: 88.3964 },
    'Barrackpore': { lat: 22.7613, lon: 88.3715 },
    'Bhilwara': { lat: 25.3501, lon: 74.6308 },
    'Muzaffarnagar': { lat: 29.4735, lon: 77.7064 },
    'Patiala': { lat: 30.3398, lon: 76.3869 },
    'Tiruppur': { lat: 11.1084, lon: 77.3410 },
    'Karnal': { lat: 29.6851, lon: 76.9898 },
    'Bathinda': { lat: 30.2101, lon: 74.9455 },
    'Bulandshahr': { lat: 28.4049, lon: 77.8497 },
    'Sonipat': { lat: 28.9895, lon: 77.0198 },
    'Firozpur': { lat: 30.9163, lon: 74.6219 },
    'Mirzapur': { lat: 25.1348, lon: 82.5825 },
    'Raebareli': { lat: 26.2294, lon: 81.2497 },
    'Kollam': { lat: 8.8906, lon: 76.6099 },
    'Khandwa': { lat: 21.8254, lon: 76.4736 },
    'Nizamabad': { lat: 18.6725, lon: 78.0941 },
    'Bhind': { lat: 26.5577, lon: 78.7850 },
    'Bikaner': { lat: 28.0229, lon: 73.1872 },
    'Ozhukarai': { lat: 11.9315, lon: 79.7897 },
    'Siliguri': { lat: 26.7271, lon: 88.3951 },
    'Panipat': { lat: 29.3909, lon: 76.9635 },
    'Fatehabad': { lat: 29.5185, lon: 75.4529 },
    'Saharsa': { lat: 25.8817, lon: 86.5988 },
    'Danapur': { lat: 25.6106, lon: 85.0440 },
    'Serampore': { lat: 22.7478, lon: 88.3426 },
    'Sultan Pur Majra': { lat: 28.6572, lon: 77.0283 },
    'Guntakal': { lat: 15.1638, lon: 77.9283 },
    'Unnao': { lat: 26.5381, lon: 80.4329 },
    'Chinsurah': { lat: 22.8966, lon: 88.3926 },
    'Alappuzha': { lat: 9.4972, lon: 76.3384 },
    'Kottayam': { lat: 9.5916, lon: 76.5212 },
    'Machilipatnam': { lat: 16.1873, lon: 81.1333 },
    'Shimla': { lat: 31.1048, lon: 77.1734 },
    'Rourkela': { lat: 22.2519, lon: 84.8858 },
    'Durg': { lat: 21.1910, lon: 81.2849 },
    'Malappuram': { lat: 11.0583, lon: 76.0713 },
    'Dindigul': { lat: 10.3673, lon: 77.9803 },
    'Rohtak': { lat: 28.8955, lon: 76.6066 },
    'Korba': { lat: 22.3498, lon: 82.7289 },
    'Bokaro': { lat: 23.6782, lon: 86.1518 },
    'Berhampur': { lat: 19.3110, lon: 84.7876 },
    'Muzaffarpur': { lat: 26.1216, lon: 85.3902 },
    'Nadiad': { lat: 22.6969, lon: 72.5856 },
    'Davanagere': { lat: 14.4637, lon: 75.9254 },
    'Kozhikode': { lat: 11.2588, lon: 75.7804 },
    'Akbarpur': { lat: 26.4399, lon: 82.5463 },
    'Rajpur Sonarpur': { lat: 22.4136, lon: 88.4197 },
    'Bongaigaon': { lat: 26.4833, lon: 90.5638 },
    'Deoghar': { lat: 24.4867, lon: 86.7037 },
    'Pali': { lat: 25.7714, lon: 73.3234 },
    'Ramagundam': { lat: 18.7596, lon: 79.4502 },
    'Silchar': { lat: 24.8317, lon: 92.7952 },
    'Haridwar': { lat: 29.9457, lon: 78.1642 },
    'Vijayanagaram': { lat: 18.1178, lon: 83.4187 },
    'Tenali': { lat: 16.2377, lon: 80.5704 },
    'Nagercoil': { lat: 8.1751, lon: 77.4383 },
    'Sri Ganganagar': { lat: 29.9157, lon: 73.8793 },
    'Karawal Nagar': { lat: 28.8251, lon: 77.2733 },
    'Mango': { lat: 22.8456, lon: 86.4284 },
    'Thanjavur': { lat: 10.7869, lon: 79.1313 },
    'Uluberia': { lat: 22.4707, lon: 88.1184 },
    'Murwara': { lat: 23.8426, lon: 80.3689 },
    'Sambalpur': { lat: 21.4782, lon: 84.7625 },
    'Singrauli': { lat: 24.1505, lon: 82.6689 },
    'Secunderabad': { lat: 17.4396, lon: 78.4982 },
    'Naihati': { lat: 22.5877, lon: 88.4222 },
    'Yamunanagar': { lat: 30.1369, lon: 77.2881 },
    'Bidhan Nagar': { lat: 22.5935, lon: 88.4162 },
    'Pallavaram': { lat: 12.9319, lon: 80.1493 },
    'Bidar': { lat: 17.9189, lon: 77.5291 },
    'Munger': { lat: 25.3739, lon: 86.4739 },
    'Panchkula': { lat: 30.6942, lon: 76.8605 },
    'Burhanpur': { lat: 21.3266, lon: 76.2167 },
    'Agartala': { lat: 23.8315, lon: 91.2868 },
    'Darbhanga': { lat: 26.1584, lon: 85.8843 },
    'Bally': { lat: 22.6538, lon: 88.3476 },
    'Aizawl': { lat: 23.7271, lon: 92.7176 },
    'Dewas': { lat: 22.7668, lon: 76.0610 },
    'Madhyamgram': { lat: 22.6989, lon: 88.4162 },
    'Bhiwani': { lat: 28.8112, lon: 76.1329 },
    'Berhampore': { lat: 24.0948, lon: 88.2532 },
    'Ambala': { lat: 30.3781, lon: 76.7843 },
    'Morbi': { lat: 22.8173, lon: 70.8314 },
    'Fatehpur': { lat: 25.7936, lon: 80.7993 },
    'Raichur': { lat: 16.2076, lon: 77.3463 },
    'Kulti': { lat: 23.7347, lon: 86.8800 },
    'Shivpuri': { lat: 25.4339, lon: 77.6533 },
    'Surendranagar Dudhrej': { lat: 22.5977, lon: 71.6390 },
    'Chittoor': { lat: 13.2170, lon: 79.1005 },
    'Bhusawal': { lat: 21.0467, lon: 75.7879 },
    'Orai': { lat: 25.9472, lon: 79.4539 },
    'Bahraich': { lat: 27.5756, lon: 81.5968 },
    'Phusro': { lat: 23.6833, lon: 86.4186 },
    'Vellore': { lat: 12.9165, lon: 79.1325 },
    'Mehsana': { lat: 23.5880, lon: 72.3693 },
    'Raiganj': { lat: 25.6209, lon: 88.1230 },
    'Sirsa': { lat: 29.5405, lon: 75.0246 },
    'Guntur': { lat: 16.3066, lon: 80.4365 },
    'Narasaraopet': { lat: 16.2337, lon: 80.0525 },
    'Dharmavaram': { lat: 14.4144, lon: 77.7192 },
    'Eluru': { lat: 16.7070, lon: 81.1055 },
    'Kadapa': { lat: 14.4762, lon: 78.8242 },
    'Kakinada': { lat: 16.9891, lon: 82.2475 },
    'Tirupati': { lat: 13.6288, lon: 79.4186 },
    'Rajahmundry': { lat: 17.0005, lon: 81.8040 },
    'Kurnool': { lat: 15.8281, lon: 78.0373 },
    'Chilakaluripet': { lat: 16.0992, lon: 80.2514 },
    'Gudivada': { lat: 16.4366, lon: 80.9964 },
    'Ongole': { lat: 15.5055, lon: 80.0494 },
    'Nandyal': { lat: 15.4866, lon: 78.4849 },
    'Madanapalle': { lat: 13.5502, lon: 78.5039 },
    'Bhimavaram': { lat: 16.5462, lon: 81.5258 },
    'Amalapuram': { lat: 16.5786, lon: 82.2386 },
    'Chirala': { lat: 15.8246, lon: 80.3522 },
    'Bapatla': { lat: 15.9067, lon: 80.4708 },
    'Tadipatri': { lat: 14.9075, lon: 78.0156 },
    'Hindupur': { lat: 13.8289, lon: 77.4895 },
    'Tadepalligudem': { lat: 16.8126, lon: 81.5013 },
    'Palakollu': { lat: 16.5086, lon: 81.7324 },
    'Jammalamadugu': { lat: 14.6426, lon: 78.3976 },
    'Yemmiganur': { lat: 15.7357, lon: 77.4767 },
    'Markapur': { lat: 15.7416, lon: 79.2733 },
    'Vinukonda': { lat: 16.3583, lon: 79.7498 },
    'Punganur': { lat: 13.3667, lon: 78.5732 },
    'Srisailam': { lat: 16.0743, lon: 78.8718 },
    'Macherla': { lat: 16.4836, lon: 79.4295 },
    'Nagarjunakonda': { lat: 16.5305, lon: 79.3198 },
    'Kothagudem': { lat: 17.6027, lon: 80.6185 },
    'Bhadrachalam': { lat: 17.6674, lon: 80.8856 },
    'Manuguru': { lat: 17.9936, lon: 80.9486 },
    'Mahbubnagar': { lat: 16.7376, lon: 77.9837 },
    'Medak': { lat: 18.0427, lon: 78.2680 },
    'Sangareddy': { lat: 17.8062, lon: 78.0866 },
    'Nalgonda': { lat: 17.0582, lon: 79.2670 },
    'Miryalaguda': { lat: 16.8661, lon: 79.4912 },
    'Suryapet': { lat: 16.8558, lon: 79.6141 },
    'Bhongir': { lat: 17.5068, lon: 78.8893 },
    'Jangaon': { lat: 17.7184, lon: 78.8667 },
    'Jagitial': { lat: 18.7855, lon: 79.4682 },
    'Peddapalli': { lat: 18.6152, lon: 79.5905 },
    'Mancherial': { lat: 18.5541, lon: 79.3694 },
    'Bellampalli': { lat: 19.0235, lon: 79.4866 },
    'Mandamarri': { lat: 18.8398, lon: 79.4790 },
    'Asifabad': { lat: 19.3575, lon: 79.2924 },
    'Kagaznagar': { lat: 19.3274, lon: 79.5456 },
    'Chinnur': { lat: 18.8678, lon: 79.5075 },
    'Sircilla': { lat: 18.4036, lon: 78.8406 },
    'Siddipet': { lat: 18.1007, lon: 78.8469 },
    'Gajwel': { lat: 18.1344, lon: 78.6835 },
    'Medchal': { lat: 17.6296, lon: 78.4836 },
    'Shamirpet': { lat: 17.5415, lon: 78.5417 },
    'Uppal': { lat: 17.4985, lon: 78.5620 },
    'Lal Bahadur Nagar': { lat: 17.4628, lon: 78.5466 },
    'Kukatpally': { lat: 17.5198, lon: 78.3959 },
    'Miyapur': { lat: 17.4962, lon: 78.3556 },
    'Madhapur': { lat: 17.4499, lon: 78.3766 },
    'Financial District': { lat: 17.4350, lon: 78.3480 },
    'HITEC City': { lat: 17.4350, lon: 78.3480 },
    'Cyberabad': { lat: 17.4350, lon: 78.3480 }
};

// DOM Elements (will be initialized after DOM loads)
let themeToggle, loginModal, loginForm, loginBtn, logoutBtn, closeLogin;
let detectBtn, batchBtn, loadingOverlay, loadingText, resultsSection;
let resultImage, comparisonSlider, sliderHandle;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM elements after DOM is loaded
    themeToggle = document.getElementById('themeToggle');
    loginModal = document.getElementById('loginModal');
    loginForm = document.getElementById('loginForm');
    loginBtn = document.getElementById('loginBtn');
    logoutBtn = document.getElementById('logoutBtn');
    closeLogin = document.getElementById('closeLogin');
    detectBtn = document.getElementById('detectBtn');
    batchBtn = document.getElementById('batchBtn');
    loadingOverlay = document.getElementById('loadingOverlay');
    loadingText = document.getElementById('loadingText');
    resultsSection = document.getElementById('resultsSection');
    resultImage = document.getElementById('resultImage');
    comparisonSlider = document.getElementById('comparisonSlider');
    sliderHandle = document.getElementById('sliderHandle');
    
    initializeTheme();
    initializeDetectionMap();
    // Don't initialize clustering map on load - it'll initialize when page is opened
    // initializeClusteringMap();
    initializeEventListeners();
    initializeSliders();
    initializeWebSocket();
    checkAuth();
    initializeCustomCursor();
    
    // Initialize charts on page load
    initializeChartsOnLoad();
    
    // Load reports data
    loadReportsData();
    
    // Setup navigation
    setupNavigation();
});

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = savedTheme + '-mode';
    updateThemeIcon();
}

function toggleTheme() {
    const body = document.body;
    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        localStorage.setItem('theme', 'light');
    }
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = themeToggle.querySelector('i');
    if (document.body.classList.contains('dark-mode')) {
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }
}

// Detection Page Map Initialization
function initializeDetectionMap() {
    const container = document.getElementById('detectionMap');
    
    if (!container) {
        console.error('Detection map container not found');
        return;
    }
    
    console.log('Initializing detection page map...');
    
    try {
        if (typeof L !== 'undefined') {
            console.log('Initializing Leaflet detection map');
            container.innerHTML = '';
            
            detectionMap = L.map(container).setView([20.5937, 78.9629], 5); // Centered on India
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(detectionMap);
            
            // Add click handler
            detectionMap.on('click', function(e) {
                const lat = e.latlng.lat;
                const lon = e.latlng.lon;
                document.getElementById('latitude').value = lat.toFixed(6);
                document.getElementById('longitude').value = lon.toFixed(6);
                updateCoordinatesDisplay(lat, lon);
                showToast('Location selected: ' + lat.toFixed(4) + ', ' + lon.toFixed(4), 'info');
                
                // Add marker
                if (detectionMarker) {
                    detectionMap.removeLayer(detectionMarker);
                }
                detectionMarker = L.marker([lat, lon]).addTo(detectionMap);
            });
            
            console.log('Detection map initialized successfully');
        } else {
            console.error('Leaflet not available');
            container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">Map unavailable</div>';
        }
    } catch (error) {
        console.error('Detection map initialization error:', error);
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">Map initialization failed</div>';
    }
}

function updateCoordinatesDisplay(lat, lon) {
    const latDisplay = document.getElementById('displayLat');
    const lonDisplay = document.getElementById('displayLon');
    
    // Only update if elements exist
    if (latDisplay) latDisplay.textContent = lat.toFixed(4);
    if (lonDisplay) lonDisplay.textContent = lon.toFixed(4);
    
    // Update satellite scan data
    updateSatelliteScanData(lat, lon);
    
    // Fetch satellite image
    fetchSatelliteImage(lat, lon);
    
    // Update map view if Leaflet map exists
    if (window.leafletMap) {
        window.leafletMap.setView([lat, lon], 10);
        
        // Add or update marker
        if (window.currentMarker) {
            window.leafletMap.removeLayer(window.currentMarker);
        }
        window.currentMarker = L.marker([lat, lon]).addTo(window.leafletMap);
    }
    
    // Update detection map if exists
    if (detectionMap) {
        detectionMap.setView([lat, lon], 10);
        
        // Add or update marker
        if (detectionMarker) {
            detectionMap.removeLayer(detectionMarker);
        }
        detectionMarker = L.marker([lat, lon]).addTo(detectionMap);
    }
}

// Fetch satellite image from backend
async function fetchSatelliteImage(lat, lon) {
    const satelliteImage = document.getElementById('satelliteImage');
    const satelliteLoading = document.getElementById('satelliteLoading');
    const satelliteError = document.getElementById('satelliteError');
    const imageCoordinates = document.getElementById('imageCoordinates');
    
    if (!satelliteImage || !satelliteLoading || !satelliteError) {
        return;
    }
    
    // Show loading state
    satelliteImage.style.display = 'none';
    satelliteLoading.style.display = 'flex';
    satelliteError.style.display = 'none';
    if (imageCoordinates) imageCoordinates.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE_URL}/satellite-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lon, zoom: 13 })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.image_data) {
                satelliteImage.src = `data:image/png;base64,${data.image_data}`;
                satelliteImage.style.display = 'block';
                satelliteLoading.style.display = 'none';
                if (imageCoordinates) imageCoordinates.style.display = 'flex';
                
                // Store image bounds for coordinate calculation
                satelliteImage.dataset.centerLat = lat;
                satelliteImage.dataset.centerLon = lon;
                satelliteImage.dataset.delta = 0.05;
            } else {
                throw new Error('Invalid response data');
            }
        } else {
            throw new Error('Failed to fetch satellite image');
        }
    } catch (error) {
        console.error('Error fetching satellite image:', error);
        satelliteLoading.style.display = 'none';
        satelliteError.style.display = 'flex';
        
        // Fallback: Use OpenStreetMap with satellite layer via Leaflet
        // Using a simpler approach with a static map service
        const zoom = 13;
        const bbox = `${lon - 0.01},${lat - 0.01},${lon + 0.01},${lat + 0.01}`;
        const fallbackUrl = `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=${bbox}&bboxSR=4326&layers=&layerDefs=&size=400,400&imageSR=4326&format=png&transparent=false&dpi=96&time=&f=image`;
        
        satelliteImage.src = fallbackUrl;
        satelliteImage.style.display = 'block';
        satelliteError.style.display = 'none';
        if (imageCoordinates) imageCoordinates.style.display = 'flex';
        
        // Store image bounds for coordinate calculation
        satelliteImage.dataset.centerLat = lat;
        satelliteImage.dataset.centerLon = lon;
        satelliteImage.dataset.delta = 0.01;
    }
}

// Update satellite scan display with real data
function updateSatelliteScanData(lat, lon) {
    const scanTarget = document.getElementById('scanTarget');
    const scanStatus = document.getElementById('scanStatus');
    const scanSignal = document.getElementById('scanSignal');
    
    if (scanTarget && scanStatus && scanSignal) {
        // Update target coordinates
        scanTarget.textContent = `${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`;
        
        // Update status based on current page
        const detectionPage = document.getElementById('page-detection');
        if (detectionPage && detectionPage.style.display !== 'none') {
            scanStatus.textContent = 'SCANNING';
            scanStatus.style.color = '#00ff00';
        } else {
            scanStatus.textContent = 'ACTIVE';
            scanStatus.style.color = '#667eea';
        }
        
        // Calculate signal strength based on location (simulated)
        const signalStrength = Math.floor(Math.random() * 30) + 70; // 70-100%
        scanSignal.textContent = `${signalStrength}%`;
        
        // Color code signal strength
        if (signalStrength >= 90) {
            scanSignal.style.color = '#00ff00';
        } else if (signalStrength >= 70) {
            scanSignal.style.color = '#ffff00';
        } else {
            scanSignal.style.color = '#ff0000';
        }
    }
}

// Periodically update satellite signal strength
setInterval(() => {
    const scanSignal = document.getElementById('scanSignal');
    const scanTarget = document.getElementById('scanTarget');
    
    if (scanSignal && scanTarget) {
        // Only update if we have a target (not SEARCHING)
        if (scanTarget.textContent !== 'SEARCHING') {
            const signalStrength = Math.floor(Math.random() * 30) + 70; // 70-100%
            scanSignal.textContent = `${signalStrength}%`;
            
            // Color code signal strength
            if (signalStrength >= 90) {
                scanSignal.style.color = '#00ff00';
            } else if (signalStrength >= 70) {
                scanSignal.style.color = '#ffff00';
            } else {
                scanSignal.style.color = '#ff0000';
            }
        }
    }
}, 2000); // Update every 2 seconds

// WebSocket Connection
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//127.0.0.1:8000/ws`);
    
    ws.onopen = () => {
        updateConnectionStatus(true);
        addLog('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
        updateConnectionStatus(false);
        addLog('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        addLog('WebSocket error: ' + error);
    };
}

function updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (connected) {
        statusDot.classList.remove('disconnected');
        statusText.textContent = 'Connected';
    } else {
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
    }
}

function handleWebSocketMessage(data) {
    if (data.type === 'progress') {
        updateProgress(data.status, data.progress, data.message);
    } else if (data.type === 'echo') {
        // Handle echo if needed
    }
}

function updateProgress(status, progress, message) {
    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    progressBar.style.width = progress + '%';
    progressText.textContent = Math.round(progress) + '%';
    
    // Update progress steps
    const stepMap = {
        'loading': 'step-loading',
        'preprocessing': 'step-preprocessing',
        'detecting': 'step-detecting',
        'fusing': 'step-fusing',
        'complete': 'step-complete',
        'error': 'step-complete'
    };
    
    // Reset all steps
    document.querySelectorAll('.progress-step').forEach(step => {
        step.classList.remove('active', 'complete');
    });
    
    // Activate current and previous steps
    const steps = ['loading', 'preprocessing', 'detecting', 'fusing', 'complete'];
    const currentIndex = steps.indexOf(status);
    
    for (let i = 0; i <= currentIndex; i++) {
        const stepId = stepMap[steps[i]];
        const stepElement = document.getElementById(stepId);
        if (stepElement) {
            if (i < currentIndex) {
                stepElement.classList.add('complete');
            } else {
                stepElement.classList.add('active');
            }
        }
    }
    
    // Add log entry
    addLog(message);
}

function addLog(message) {
    const logContainer = document.getElementById('logContainer');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Authentication
function checkAuth() {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
        authToken = savedToken;
        currentUser = JSON.parse(localStorage.getItem('currentUser'));
        updateAuthUI(true);
    }
}

async function login(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        currentUser = { username, role: data.role };
        
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        updateAuthUI(true);
        loginModal.style.display = 'none';
        showToast('Login successful!', 'success');
        
        // Enable batch button for admin
        if (data.role === 'admin') {
            batchBtn.disabled = false;
        }
        
    } catch (error) {
        showToast('Login failed: ' + error.message, 'error');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    updateAuthUI(false);
    batchBtn.disabled = true;
    showToast('Logged out successfully', 'info');
}

function updateAuthUI(isLoggedIn) {
    if (isLoggedIn) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-flex';
        logoutBtn.innerHTML = `<i class="fas fa-sign-out-alt"></i> ${currentUser.username}`;
    } else {
        loginBtn.style.display = 'inline-flex';
        logoutBtn.style.display = 'none';
    }
}

// Event Listeners
function initializeEventListeners() {
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);
    
    // Login modal
    loginBtn.addEventListener('click', () => {
        loginModal.style.display = 'flex';
    });
    
    closeLogin.addEventListener('click', () => {
        loginModal.style.display = 'none';
    });
    
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        login(username, password);
    });
    
    logoutBtn.addEventListener('click', logout);
    
    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.style.display = 'none';
        }
    });
    
    // Detection - Use event delegation since button might be in hidden page
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('#detectBtn');
        if (btn) {
            console.log('Detection button clicked via delegation');
            e.preventDefault();
            runDetection();
        }
    });
    
    // Quick locations
    document.querySelectorAll('.location-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = parseFloat(btn.dataset.lat);
            const lon = parseFloat(btn.dataset.lon);
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lon;
            updateCoordinatesDisplay(lat, lon);
        });
    });
    
    // Get current location
    const getLocationBtn = document.getElementById('getLocationBtn');
    if (getLocationBtn) {
        getLocationBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                showToast('Geolocation is not supported by your browser', 'error');
                return;
            }
            
            showToast('Getting your location...', 'info');
            getLocationBtn.disabled = true;
            getLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    document.getElementById('latitude').value = lat.toFixed(6);
                    document.getElementById('longitude').value = lon.toFixed(6);
                    updateCoordinatesDisplay(lat, lon);
                    
                    showToast(`Location found: ${lat.toFixed(4)}, ${lon.toFixed(4)}`, 'success');
                    getLocationBtn.disabled = false;
                    getLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get My Location';
                },
                (error) => {
                    let errorMessage = 'Unable to retrieve your location';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage = 'Location permission denied. Please enable location access.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage = 'Location information is unavailable.';
                            break;
                        case error.TIMEOUT:
                            errorMessage = 'Location request timed out. Using last known location.';
                            break;
                    }
                    showToast(errorMessage, 'error');
                    getLocationBtn.disabled = false;
                    getLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get My Location';
                },
                {
                    enableHighAccuracy: false,
                    timeout: 5000,
                    maximumAge: 60000
                }
            );
        });
    }
    
    // Search location using OpenStreetMap Nominatim API (free, no API key needed)
    const searchLocationBtn = document.getElementById('searchLocationBtn');
    if (searchLocationBtn) {
        searchLocationBtn.addEventListener('click', async () => {
            const locationName = document.getElementById('locationSearch').value.trim();
            
            if (!locationName) {
                showToast('Please enter a location name', 'error');
                return;
            }
            
            searchLocationBtn.disabled = true;
            searchLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
            
            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationName)}&limit=1`
                );
                const data = await response.json();
                
                if (data && data.length > 0) {
                    const lat = parseFloat(data[0].lat);
                    const lon = parseFloat(data[0].lon);
                    const displayName = data[0].display_name;
                    
                    document.getElementById('latitude').value = lat.toFixed(6);
                    document.getElementById('longitude').value = lon.toFixed(6);
                    updateCoordinatesDisplay(lat, lon);
                    
                    if (detectionMap) {
                        detectionMap.setView([lat, lon], 13);
                    }
                    
                    showToast(`Location found: ${displayName.split(',')[0]} (${lat.toFixed(4)}, ${lon.toFixed(4)})`, 'success');
                } else {
                    showToast(`Location "${locationName}" not found. Please try a different name.`, 'error');
                }
            } catch (error) {
                console.error('Geocoding error:', error);
                showToast('Failed to search location. Please check your internet connection.', 'error');
            } finally {
                searchLocationBtn.disabled = false;
                searchLocationBtn.innerHTML = '<i class="fas fa-search"></i> Search';
            }
        });
    }
    
    // Location autocomplete suggestions
    const locationSearchInput = document.getElementById('locationSearch');
    const locationSuggestions = document.getElementById('locationSuggestions');
    let debounceTimer;
    
    if (locationSearchInput && locationSuggestions) {
        locationSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(debounceTimer);
            
            if (query.length < 2) {
                locationSuggestions.classList.remove('active');
                locationSuggestions.innerHTML = '';
                return;
            }
            
            debounceTimer = setTimeout(async () => {
                try {
                    const response = await fetch(
                        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`
                    );
                    const data = await response.json();
                    
                    if (data && data.length > 0) {
                        locationSuggestions.innerHTML = '';
                        
                        data.forEach(location => {
                            const suggestionItem = document.createElement('div');
                            suggestionItem.className = 'suggestion-item';
                            
                            const name = location.display_name.split(',')[0];
                            const details = location.display_name.substring(name.length + 2);
                            
                            suggestionItem.innerHTML = `
                                <div class="suggestion-name">${name}</div>
                                <div class="suggestion-details">${details}</div>
                            `;
                            
                            suggestionItem.addEventListener('click', () => {
                                const lat = parseFloat(location.lat);
                                const lon = parseFloat(location.lon);
                                
                                locationSearchInput.value = name;
                                document.getElementById('latitude').value = lat.toFixed(6);
                                document.getElementById('longitude').value = lon.toFixed(6);
                                updateCoordinatesDisplay(lat, lon);
                                
                                if (detectionMap) {
                                    detectionMap.setView([lat, lon], 13);
                                }
                                
                                locationSuggestions.classList.remove('active');
                                locationSuggestions.innerHTML = '';
                                
                                showToast(`Location selected: ${name} (${lat.toFixed(4)}, ${lon.toFixed(4)})`, 'success');
                            });
                            
                            locationSuggestions.appendChild(suggestionItem);
                        });
                        
                        locationSuggestions.classList.add('active');
                    } else {
                        locationSuggestions.classList.remove('active');
                        locationSuggestions.innerHTML = '';
                    }
                } catch (error) {
                    console.error('Autocomplete error:', error);
                }
            }, 300);
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!locationSearchInput.contains(e.target) && !locationSuggestions.contains(e.target)) {
                locationSuggestions.classList.remove('active');
            }
        });
    }
    
    // Hero action buttons
    const heroButtons = document.querySelectorAll('.hero-actions .btn');
    heroButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const page = e.currentTarget.dataset.page;
            if (page) {
                switchPage(page);
                // Scroll to navigation
                document.querySelector('.main-nav').scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Navigation buttons - REMOVED to avoid conflict with setupNavigation()
    
    // Detection button
    if (detectBtn) {
        detectBtn.addEventListener('click', runDetection);
    }
    
    // Image download
    const downloadBtn = document.getElementById('downloadImage');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadCurrentImage);
    }
    
    // PDF export (may not exist in new layout)
    const exportPdfBtn = document.getElementById('exportPdf');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', exportToPdf);
    }
    
    // Fullscreen
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreen);
    }
    
    // Image viewer tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentImageView = e.target.dataset.view;
            loadImageView(currentImageView);
        });
    });
    
    // Comparison slider
    initializeComparisonSlider();
    
    // Image coordinate tracking
    const satelliteImage = document.getElementById('satelliteImage');
    if (satelliteImage) {
        satelliteImage.addEventListener('mousemove', function(e) {
            const rect = satelliteImage.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const centerLat = parseFloat(satelliteImage.dataset.centerLat) || 0;
            const centerLon = parseFloat(satelliteImage.dataset.centerLon) || 0;
            const delta = parseFloat(satelliteImage.dataset.delta) || 0.05;
            
            // Calculate offset from center (normalized -1 to 1)
            const offsetX = (x - centerX) / centerX;
            const offsetY = (centerY - y) / centerY; // Invert Y because latitude increases upward
            
            // Calculate actual coordinates
            const cursorLat = centerLat + (offsetY * delta);
            const cursorLon = centerLon + (offsetX * delta);
            
            const cursorLatEl = document.getElementById('cursorLat');
            const cursorLonEl = document.getElementById('cursorLon');
            
            if (cursorLatEl) cursorLatEl.textContent = cursorLat.toFixed(4);
            if (cursorLonEl) cursorLonEl.textContent = cursorLon.toFixed(4);
        });
        
        satelliteImage.addEventListener('mouseleave', function() {
            const cursorLatEl = document.getElementById('cursorLat');
            const cursorLonEl = document.getElementById('cursorLon');
            
            if (cursorLatEl) cursorLatEl.textContent = '--';
            if (cursorLonEl) cursorLonEl.textContent = '--';
        });
    }
    
    console.log('Event listeners initialized');
}

// Navigation Setup
function setupNavigation() {
    console.log('Setting up navigation...');
    const navButtons = document.querySelectorAll('.nav-btn');
    console.log('Found nav buttons:', navButtons.length);
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const page = this.dataset.page;
            console.log('Nav button clicked, switching to:', page);
            
            // Remove active class from all buttons
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            
            // Hide all pages
            document.querySelectorAll('.page').forEach(p => {
                p.classList.remove('active');
                p.style.display = 'none';
            });
            
            // Hide landing page sections
            const heroSection = document.querySelector('.hero-section');
            const featuresSection = document.querySelector('.features-section');
            const vizSection = document.querySelector('.visualization-section');
            if (heroSection) heroSection.style.display = 'none';
            if (featuresSection) featuresSection.style.display = 'none';
            if (vizSection) vizSection.style.display = 'none';
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Show corresponding page
            const targetPage = document.getElementById(`page-${page}`);
            if (targetPage) {
                targetPage.classList.add('active');
                targetPage.style.display = 'block';
                console.log('Page switched to:', page, 'Element:', targetPage);
            } else {
                console.error('Page not found:', page);
            }
            
            // Reinitialize maps if needed
            if (page === 'dashboard' && window.leafletMap) {
                setTimeout(() => window.leafletMap.invalidateSize(), 100);
            }
            if (page === 'detection' && detectionMap) {
                setTimeout(() => detectionMap.invalidateSize(), 100);
            }
            if (page === 'defense') {
                // Force initialize defense map with multiple attempts
                setTimeout(() => {
                    if (!defenseMap) {
                        initializeDefenseMap();
                    } else {
                        defenseMap.invalidateSize();
                    }
                }, 100);
                setTimeout(() => {
                    if (!defenseMap) {
                        initializeDefenseMap();
                    } else {
                        defenseMap.invalidateSize();
                    }
                }, 500);
            }
            if (page === 'agriculture') {
                // Force initialize agriculture map with multiple attempts
                setTimeout(() => {
                    if (!agriMap) {
                        initializeAgriMap();
                    } else {
                        agriMap.invalidateSize();
                    }
                }, 100);
                setTimeout(() => {
                    if (!agriMap) {
                        initializeAgriMap();
                    } else {
                        agriMap.invalidateSize();
                    }
                }, 500);
            }
            if (page === 'geological') {
                // Force initialize geological map with multiple attempts
                setTimeout(() => {
                    if (!geoMap) {
                        initializeGeoMap();
                    } else {
                        geoMap.invalidateSize();
                    }
                }, 100);
                setTimeout(() => {
                    if (!geoMap) {
                        initializeGeoMap();
                    } else {
                        geoMap.invalidateSize();
                    }
                }, 500);
            }
            
            if (page === 'analysis') {
                setTimeout(() => loadSpectralBands(), 100);
                // Load RGB image automatically if detection has been run
                setTimeout(() => loadImageView('rgb'), 200);
            }
        });
    });
}

// Page Switching
function switchPage(pageName) {
    console.log('Switching to page:', pageName);
    
    // Hide all pages with force
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        page.style.display = 'none';
        page.style.visibility = 'hidden';
        page.style.opacity = '0';
        page.style.position = 'absolute';
    });
    
    // Show selected page
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
        targetPage.style.display = 'block';
        targetPage.style.visibility = 'visible';
        targetPage.style.opacity = '1';
        targetPage.style.position = 'relative';
        console.log('Page displayed:', pageName);
    } else {
        console.error('Page not found:', pageName);
    }
    
    // Reinitialize map if switching to dashboard
    if (pageName === 'dashboard' && window.leafletMap) {
        setTimeout(() => window.leafletMap.invalidateSize(), 100);
    }
    
    // Reinitialize detection map if switching to detection
    if (pageName === 'detection' && detectionMap) {
        setTimeout(() => detectionMap.invalidateSize(), 100);
    }
    
}

function initializeSliders() {
    const nComponentsSlider = document.getElementById('nComponents');
    const nComponentsValue = document.getElementById('nComponentsValue');
    const encodingDimSlider = document.getElementById('encodingDim');
    const encodingDimValue = document.getElementById('encodingDimValue');
    
    nComponentsSlider.addEventListener('input', (e) => {
        nComponentsValue.textContent = e.target.value;
    });
    
    encodingDimSlider.addEventListener('input', (e) => {
        encodingDimValue.textContent = e.target.value;
    });
}

// Detection Handler
async function runDetection() {
    console.log('runDetection function called');
    
    // Check if we're on the detection page
    const detectionPage = document.getElementById('page-detection');
    if (!detectionPage || !detectionPage.classList.contains('active')) {
        console.error('Not on detection page');
        showToast('Please navigate to the Detection page first', 'error');
        return;
    }
    
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');
    const pcaInput = document.getElementById('pcaComponents');
    const encodingInput = document.getElementById('encodingDim');
    
    if (!latInput || !lonInput) {
        console.error('Input elements not found');
        showToast('Required input fields not found', 'error');
        return;
    }
    
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);
    const nComponents = pcaInput ? parseInt(pcaInput.value) : 10;
    const encodingDim = encodingInput ? parseInt(encodingInput.value) : 8;
    const useGee = document.getElementById('useGee') ? document.getElementById('useGee').checked : false;
    const enableCache = document.getElementById('enableCache') ? document.getElementById('enableCache').checked : false;
    const useVit = document.getElementById('useVit') ? document.getElementById('useVit').checked : true;
    const useEnsemble = document.getElementById('useEnsemble') ? document.getElementById('useEnsemble').checked : true;
    const detectClouds = document.getElementById('detectClouds') ? document.getElementById('detectClouds').checked : true;
    const applyAtmosphericCorrection = document.getElementById('applyAtmosphericCorrection') ? document.getElementById('applyAtmosphericCorrection').checked : true;

    console.log('Detection parameters:', { lat, lon, nComponents, encodingDim, useGee });

    if (isNaN(lat) || isNaN(lon)) {
        console.error('Invalid coordinates:', lat, lon);
        showToast('Please enter valid coordinates', 'error');
        return;
    }

    showLoading();
    addLog('Starting detection...');

    try {
        const response = await fetch(`${API_BASE_URL}/detect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                use_gee: useGee,
                n_components: nComponents,
                encoding_dim: encodingDim,
                enable_cache: enableCache,
                use_vit: useVit,
                use_ensemble: useEnsemble,
                detect_clouds: detectClouds,
                apply_atmospheric_correction: applyAtmosphericCorrection
            })
        });

        if (!response.ok) {
            throw new Error(`Detection failed: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            addLog('Detection completed successfully');
            addLog(`Data source: ${data.data_source}`);
            addLog(`Anomalies found: ${data.anomaly_count}`);

            // Update stats
            updateStats(data);

            // Initialize charts
            initializeCharts(data);

            // Update heatmap with real data
            if (typeof initD3Visualization === 'function') {
                initD3Visualization(data);
            }

            // Update hyperspectral visualization with real data
            if (typeof initHyperspectralVisualization === 'function') {
                initHyperspectralVisualization(data);
            }

            // Load spectral band statistics
            await loadSpectralBands();

            // Automatically load RGB image in image analysis
            await loadImageView('rgb');

            showToast('Detection completed successfully!', 'success');
        } else {
            throw new Error(data.message || 'Detection failed');
        }
    } catch (error) {
        showToast('Error during detection: ' + error.message, 'error');
        addLog('Error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function updateStats(data) {
    document.getElementById('dataSource').textContent = data.data_source || '-';
    document.getElementById('processingTime').textContent = data.processing_time ? 
        data.processing_time.toFixed(2) + 's' : '-';
    document.getElementById('anomalyCount').textContent = data.anomaly_count || '-';
    document.getElementById('anomalyPercentage').textContent = data.anomaly_percentage ? 
        data.anomaly_percentage.toFixed(2) + '%' : '-';
    
    // Update advanced analysis stats
    document.getElementById('cloudCoverage').textContent = data.cloud_coverage !== null && data.cloud_coverage !== undefined ? 
        data.cloud_coverage.toFixed(1) + '%' : '--%';
    document.getElementById('ndviValue').textContent = data.ndvi !== null && data.ndvi !== undefined ? 
        data.ndvi.toFixed(3) : '--';
    document.getElementById('ndwiValue').textContent = data.ndwi !== null && data.ndwi !== undefined ? 
        data.ndwi.toFixed(3) : '--';
    document.getElementById('numClusters').textContent = data.num_clusters !== null && data.num_clusters !== undefined ? 
        data.num_clusters : '--';
    document.getElementById('materialIdentified').textContent = data.material_identified || '--';
    
    // Update data source
    const dataSourceElement = document.getElementById('dataSource');
    if (dataSourceElement) {
        dataSourceElement.textContent = data.data_source || '--';
    }
    
    // Update quick stats
    totalDetections++;
    if (data.processing_time) {
        totalProcessingTime += data.processing_time;
    }
    
    const totalDetectionsEl = document.getElementById('totalDetections');
    const avgProcessingTimeEl = document.getElementById('avgProcessingTime');
    
    if (totalDetectionsEl) {
        totalDetectionsEl.textContent = totalDetections;
    }
    
    if (avgProcessingTimeEl) {
        const avgTime = totalDetections > 0 ? (totalProcessingTime / totalDetections).toFixed(2) : '0';
        avgProcessingTimeEl.textContent = avgTime + 's';
    }
    
    // Add to detection history
    const historyItem = {
        date: new Date().toLocaleString(),
        location: `${document.getElementById('latitude').value}, ${document.getElementById('longitude').value}`,
        anomalies: data.anomaly_count || 0
    };
    detectionHistory.unshift(historyItem);
    
    // Keep only last 10 detections
    if (detectionHistory.length > 10) {
        detectionHistory.pop();
    }
    
    updateDetectionHistory();
}

function updateDetectionHistory() {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    
    historyList.innerHTML = '';
    
    if (detectionHistory.length === 0) {
        historyList.innerHTML = `
            <div class="history-item">
                <span class="history-date">-</span>
                <span class="history-location">-</span>
                <span class="history-anomalies">-</span>
            </div>
        `;
        return;
    }
    
    detectionHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <span class="history-date">${item.date}</span>
            <span class="history-location">${item.location}</span>
            <span class="history-anomalies">${item.anomalies}</span>
        `;
        historyList.appendChild(historyItem);
    });
}

async function loadImageView(viewType) {
    const imageDisplay = document.getElementById('imageDisplay');
    const placeholder = document.getElementById('imagePlaceholder');
    const resultImage = document.getElementById('resultImage');
    
    if (viewType === 'compare') {
        // Show comparison slider
        if (comparisonSlider) comparisonSlider.style.display = 'block';
        if (resultImage) resultImage.style.display = 'none';
        if (placeholder) placeholder.style.display = 'none';
        
        // Load both images
        await loadImage('rgb', 'compareBefore');
        await loadImage('overlay', 'compareAfter');
    } else {
        // Show single image
        if (comparisonSlider) comparisonSlider.style.display = 'none';
        if (resultImage) {
            resultImage.style.display = 'block';
            const loaded = await loadImage(viewType, 'resultImage');
            if (!loaded) {
                // Show placeholder if image not available
                if (placeholder) {
                    placeholder.style.display = 'block';
                    placeholder.innerHTML = `
                        <i class="fas fa-images"></i>
                        <p>Run detection to view ${viewType.toUpperCase()} image</p>
                    `;
                }
                resultImage.style.display = 'none';
            } else {
                if (placeholder) placeholder.style.display = 'none';
            }
        }
    }
}

async function loadImage(imageType, targetElementId) {
    try {
        console.log(`Loading image: ${imageType}`);
        const response = await fetch(`${API_BASE_URL}/image/${imageType}`);
        
        if (!response.ok) {
            console.error(`Failed to load ${imageType}: ${response.status}`);
            return false;
        }
        
        const data = await response.json();
        
        if (data.success && data.image_data) {
            const imgElement = document.getElementById(targetElementId);
            if (imgElement) {
                imgElement.src = `data:image/png;base64,${data.image_data}`;
                console.log(`Successfully loaded ${imageType}`);
                return true;
            } else {
                console.error(`Target element ${targetElementId} not found`);
                return false;
            }
        } else {
            console.error(`Invalid response for ${imageType}`);
            return false;
        }
    } catch (error) {
        console.error(`Error loading ${imageType}:`, error);
        return false;
    }
}

async function loadSpectralBands() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        
        if (!response.ok) {
            throw new Error('Failed to load spectral statistics');
        }
        
        const data = await response.json();
        
        // Update advanced analysis metrics
        if (data.cloud_coverage !== null && data.cloud_coverage !== undefined) {
            document.getElementById('cloudCoverage').textContent = data.cloud_coverage.toFixed(1) + '%';
        }
        if (data.ndvi !== null && data.ndvi !== undefined) {
            document.getElementById('ndviValue').textContent = data.ndvi.toFixed(3);
        }
        if (data.ndwi !== null && data.ndwi !== undefined) {
            document.getElementById('ndwiValue').textContent = data.ndwi.toFixed(3);
        }
        if (data.num_clusters !== null && data.num_clusters !== undefined) {
            document.getElementById('numClusters').textContent = data.num_clusters;
        }
        if (data.material_identified) {
            document.getElementById('materialIdentified').textContent = data.material_identified;
        }
        if (data.data_source) {
            const dataSourceElement = document.getElementById('dataSource');
            if (dataSourceElement) {
                dataSourceElement.textContent = data.data_source;
            }
        }
        
        if (data.spectral_bands) {
            // Update spectral band charts
            updateSpectralCharts(data.spectral_bands);
        } else {
            // Use default values if no data
            const defaultBands = {
                "blue": {"min": 0.1, "max": 0.8, "mean": 0.4, "std": 0.2},
                "green": {"min": 0.2, "max": 0.9, "mean": 0.5, "std": 0.2},
                "red": {"min": 0.1, "max": 0.85, "mean": 0.45, "std": 0.2},
                "nir": {"min": 0.3, "max": 0.95, "mean": 0.6, "std": 0.2},
                "swir1": {"min": 0.1, "max": 0.7, "mean": 0.4, "std": 0.15},
                "swir2": {"min": 0.05, "max": 0.6, "mean": 0.3, "std": 0.15}
            };
            updateSpectralCharts(defaultBands);
        }
    } catch (error) {
        console.error('Error loading spectral bands:', error);
        // Use default values on error
        const defaultBands = {
            "blue": {"min": 0.1, "max": 0.8, "mean": 0.4, "std": 0.2},
            "green": {"min": 0.2, "max": 0.9, "mean": 0.5, "std": 0.2},
            "red": {"min": 0.1, "max": 0.85, "mean": 0.45, "std": 0.2},
            "nir": {"min": 0.3, "max": 0.95, "mean": 0.6, "std": 0.2},
            "swir1": {"min": 0.1, "max": 0.7, "mean": 0.4, "std": 0.15},
            "swir2": {"min": 0.05, "max": 0.6, "mean": 0.3, "std": 0.15}
        };
        updateSpectralCharts(defaultBands);
    }
}

async function loadReportsData() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        
        if (!response.ok) {
            throw new Error('Failed to load reports data');
        }
        
        const data = await response.json();
        
        // Update score distribution chart
        updateScoreDistribution(data);
    } catch (error) {
        console.error('Error loading reports data:', error);
    }
}

function updateScoreDistribution(data) {
    const canvas = document.getElementById('scoreChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.parentElement.clientWidth - 20;
    canvas.height = 300;
    
    // Generate sample score distribution data
    const scores = [];
    for (let i = 0; i < 100; i++) {
        scores.push(Math.random() * 0.5 + 0.2); // Random scores between 0.2 and 0.7
    }
    
    // Create histogram
    const bins = 20;
    const histogram = new Array(bins).fill(0);
    scores.forEach(score => {
        const binIndex = Math.floor(score * bins);
        if (binIndex < bins) histogram[binIndex]++;
    });
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw histogram
    const barWidth = canvas.width / bins;
    const maxCount = Math.max(...histogram);
    
    histogram.forEach((count, i) => {
        const barHeight = (count / maxCount) * (canvas.height - 40);
        const x = i * barWidth;
        const y = canvas.height - barHeight - 20;
        
        ctx.fillStyle = '#667eea';
        ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
    });
    
    // Add labels
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    ctx.fillText('Score Distribution', 10, 20);
}

function updateSpectralCharts(spectralData) {
    // Update spectral band charts with actual band data
    updateBandChart('bandBlue', spectralData.blue, '#667eea');
    updateBandChart('bandGreen', spectralData.green, '#2ecc71');
    updateBandChart('bandRed', spectralData.red, '#e74c3c');
    updateBandChart('bandNIR', spectralData.nir, '#9b59b6');
    updateBandChart('bandSWIR1', spectralData.swir1, '#e67e22');
    updateBandChart('bandSWIR2', spectralData.swir2, '#1abc9c');
}

function updateBandChart(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    // Hide placeholder and show canvas
    const parent = canvas.parentElement;
    const placeholder = parent.querySelector('.band-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    canvas.style.display = 'block';
    
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = parent.clientWidth - 20;
    canvas.height = 100;
    
    // Create a simple bar chart showing min, mean, max
    const values = [data.min, data.mean, data.max];
    const labels = ['Min', 'Mean', 'Max'];
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw bars
    const barWidth = canvas.width / 4;
    const maxVal = Math.max(...values) * 1.1;
    
    values.forEach((val, i) => {
        const barHeight = (val / maxVal) * (canvas.height - 20);
        const x = (i + 0.5) * barWidth;
        const y = canvas.height - barHeight - 20;
        
        ctx.fillStyle = color;
        ctx.fillRect(x, y, barWidth - 10, barHeight);
        
        // Add label
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(labels[i], x + barWidth / 2 - 5, canvas.height - 5);
        
        // Add value
        ctx.fillStyle = '#666';
        ctx.fillText(val.toFixed(3), x + barWidth / 2 - 5, y - 5);
    });
}

// Charts
function initializeCharts(data) {
    console.log('Initializing charts with data:', data);
    
    // Score Distribution Chart
    const scoreCanvas = document.getElementById('scoreChart');
    if (scoreCanvas) {
        const scoreCtx = scoreCanvas.getContext('2d');
        
        if (scoreChart) {
            scoreChart.destroy();
        }
        
        const scoreData = data.scores || [0.1, 0.3, 0.5, 0.7, 0.9];
        
        scoreChart = new Chart(scoreCtx, {
            type: 'line',
            data: {
                labels: ['Min', '25%', '50%', '75%', 'Max'],
                datasets: [{
                    label: 'Anomaly Scores',
                    data: scoreData,
                    borderColor: '#00F2FF',
                    backgroundColor: 'rgba(0, 242, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#e0e0e0'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        grid: {
                            color: 'rgba(0, 242, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 242, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    }
                }
            }
        });
    }
    
    // Comparison Chart
    const comparisonCanvas = document.getElementById('comparisonChart');
    if (comparisonCanvas) {
        const comparisonCtx = comparisonCanvas.getContext('2d');
        
        if (comparisonChart) {
            comparisonChart.destroy();
        }
        
        comparisonChart = new Chart(comparisonCtx, {
            type: 'bar',
            data: {
                labels: ['RGB', 'NIR', 'SWIR'],
                datasets: [{
                    label: 'Before',
                    data: [0.3, 0.4, 0.5],
                    backgroundColor: 'rgba(255, 99, 132, 0.5)'
                }, {
                    label: 'After',
                    data: [0.5, 0.6, 0.7],
                    backgroundColor: 'rgba(0, 242, 255, 0.5)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#e0e0e0'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        grid: {
                            color: 'rgba(0, 242, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 242, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    }
                }
            }
        });
    }
}

// Initialize charts on page load
function initializeChartsOnLoad() {
    // Initialize Score Distribution chart with sample data
    const scoreCanvas = document.getElementById('scoreChart');
    if (scoreCanvas && !scoreChart) {
        const scoreCtx = scoreCanvas.getContext('2d');
        
        const sampleData = [0.1, 0.3, 0.5, 0.7, 0.9];
        
        scoreChart = new Chart(scoreCtx, {
            type: 'line',
            data: {
                labels: ['Min', '25%', '50%', '75%', 'Max'],
                datasets: [{
                    label: 'Anomaly Scores',
                    data: sampleData,
                    borderColor: '#00F2FF',
                    backgroundColor: 'rgba(0, 242, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#e0e0e0'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        grid: {
                            color: 'rgba(0, 242, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 242, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    }
                }
            }
        });
    }
    
    // Initialize spectral band charts with default data
    const defaultBands = {
        "blue": {"min": 0.1, "max": 0.8, "mean": 0.4, "std": 0.2},
        "green": {"min": 0.2, "max": 0.9, "mean": 0.5, "std": 0.2},
        "red": {"min": 0.1, "max": 0.85, "mean": 0.45, "std": 0.2},
        "nir": {"min": 0.3, "max": 0.95, "mean": 0.6, "std": 0.2},
        "swir1": {"min": 0.1, "max": 0.7, "mean": 0.4, "std": 0.15},
        "swir2": {"min": 0.05, "max": 0.6, "mean": 0.3, "std": 0.15}
    };
    updateSpectralCharts(defaultBands);
}

// Comparison Slider
function initializeComparisonSlider() {
// Check if comparison slider elements exist (may not exist in new layout)
if (!sliderHandle || !comparisonSlider) {
    console.log('Comparison slider elements not found, skipping initialization');
    return;
}
    if (!sliderHandle || !comparisonSlider) {
        console.log('Comparison slider elements not found, skipping initialization');
        return;
    }
    
    let isDragging = false;
    
    sliderHandle.addEventListener('mousedown', () => {
        isDragging = true;
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const rect = comparisonSlider.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
        
        sliderHandle.style.left = percentage + '%';
        document.querySelector('.compare-before').style.width = percentage + '%';
    });
    
    // Touch support
    sliderHandle.addEventListener('touchstart', () => {
        isDragging = true;
    });
    
    document.addEventListener('touchend', () => {
        isDragging = false;
    });
    
    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        
        const rect = comparisonSlider.getBoundingClientRect();
        const x = e.touches[0].clientX - rect.left;
        const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
        
        sliderHandle.style.left = percentage + '%';
        document.querySelector('.compare-before').style.width = percentage + '%';
    });
}

// Download
function downloadCurrentImage() {
    if (currentImageView === 'compare') {
        showToast('Cannot download comparison view. Select a single image.', 'info');
        return;
    }
    
    const img = document.getElementById('resultImage');
    if (!img.src) {
        showToast('No image to download', 'error');
        return;
    }
    
    const link = document.createElement('a');
    link.download = `anomaly_detection_${currentImageView}.png`;
    link.href = img.src;
    link.click();
    
    showToast('Image downloaded!', 'success');
}

// PDF Export (simplified - would need jsPDF in production)
function exportToPdf() {
    showToast('PDF export feature requires jsPDF library. Image download available.', 'info');
    downloadCurrentImage();
}

// Fullscreen
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

// Loading Overlay
function showLoading(text) {
    loadingText.textContent = text;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
    
    toast.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    container.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Defense Map Initialization
let defenseMap = null;
function initializeDefenseMap() {
    const mapContainer = document.getElementById('defenseMap');
    if (!mapContainer) {
        console.log('Defense map container not found');
        return;
    }
    
    // Always initialize the map regardless of visibility
    if (defenseMap) {
        console.log('Defense map already exists, invalidating size');
        setTimeout(() => defenseMap.invalidateSize(), 100);
        return;
    }
    
    console.log('Initializing Defense map...');
    try {
        defenseMap = L.map('defenseMap', {
            center: [40.7128, -74.0060],
            zoom: 13
        });
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(defenseMap);
        
        console.log('Defense map initialized successfully');
    } catch (error) {
        console.error('Error initializing Defense map:', error);
    }
}

// Agriculture Map Initialization
let agriMap = null;
function initializeAgriMap() {
    const mapContainer = document.getElementById('agriMap');
    if (!mapContainer) {
        console.log('Agriculture map container not found');
        return;
    }
    
    // Always initialize the map regardless of visibility
    if (agriMap) {
        console.log('Agriculture map already exists, invalidating size');
        setTimeout(() => agriMap.invalidateSize(), 100);
        return;
    }
    
    console.log('Initializing Agriculture map...');
    try {
        agriMap = L.map('agriMap', {
            center: [40.7128, -74.0060],
            zoom: 13
        });
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(agriMap);
        
        console.log('Agriculture map initialized successfully');
    } catch (error) {
        console.error('Error initializing Agriculture map:', error);
    }
}

// Geological Map Initialization
let geoMap = null;
function initializeGeoMap() {
    const mapContainer = document.getElementById('geoMap');
    if (!mapContainer) {
        console.log('Geological map container not found');
        return;
    }
    
    // Always initialize the map regardless of visibility
    if (geoMap) {
        console.log('Geological map already exists, invalidating size');
        setTimeout(() => geoMap.invalidateSize(), 100);
        return;
    }
    
    console.log('Initializing Geological map...');
    try {
        geoMap = L.map('geoMap', {
            center: [40.7128, -74.0060],
            zoom: 13
        });
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(geoMap);
        
        console.log('Geological map initialized successfully');
    } catch (error) {
        console.error('Error initializing Geological map:', error);
    }
}

// Defense Detection Handler
async function runDefenseDetection() {
    console.log('Running Defense detection...');
    
    const lat = parseFloat(document.getElementById('defenseLatitude').value);
    const lon = parseFloat(document.getElementById('defenseLongitude').value);
    const targetType = document.getElementById('defenseTargetType').value;
    const useViT = document.getElementById('defenseUseViT').checked;
    const useEnsemble = document.getElementById('defenseUseEnsemble').checked;
    
    if (isNaN(lat) || isNaN(lon)) {
        showToast('Please enter valid coordinates', 'error');
        return;
    }
    
    showLoading();
    addLog('Starting defense detection...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/detect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat,
                lon,
                use_gee: false,
                use_vit: useViT,
                use_ensemble: useEnsemble,
                detect_clouds: true,
                apply_atmospheric_correction: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            hideLoading();
            addLog(`Defense detection complete. Anomalies: ${data.anomaly_count}`);
            addLog(`Material identified: ${data.material_identified || 'N/A'}`);
            
            // Display results
            const resultsDiv = document.getElementById('defenseResults');
            resultsDiv.innerHTML = `
                <div class="result-item">
                    <label>Target Type:</label>
                    <span>${targetType}</span>
                </div>
                <div class="result-item">
                    <label>Targets Detected:</label>
                    <span>${data.anomaly_count}</span>
                </div>
                <div class="result-item">
                    <label>Material:</label>
                    <span>${data.material_identified || 'Unknown'}</span>
                </div>
                <div class="result-item">
                    <label>Confidence:</label>
                    <span>${(1 - data.fused_threshold).toFixed(2)}</span>
                </div>
            `;
            
            // Update defense map with detection results
            if (defenseMap) {
                // Clear existing markers
                defenseMap.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        defenseMap.removeLayer(layer);
                    }
                });
                
                // Add marker at detection location
                const marker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: '<div style="background: #ff0000; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
                        iconSize: [20, 20]
                    })
                }).addTo(defenseMap);
                
                marker.bindPopup(`
                    <b>Defense Target Detected</b><br>
                    Type: ${targetType}<br>
                    Anomalies: ${data.anomaly_count}<br>
                    Material: ${data.material_identified || 'Unknown'}
                `);
                
                // Center map on detection
                defenseMap.setView([lat, lon], 15);
            }
            
            showToast('Defense detection complete', 'success');
        } else {
            throw new Error(data.detail || 'Detection failed');
        }
    } catch (error) {
        hideLoading();
        console.error('Defense detection error:', error);
        showToast('Defense detection failed: ' + error.message, 'error');
    }
}

// Agriculture Detection Handler
async function runAgriDetection() {
    console.log('Running Agriculture analysis...');
    
    const lat = parseFloat(document.getElementById('agriLatitude').value);
    const lon = parseFloat(document.getElementById('agriLongitude').value);
    const cropType = document.getElementById('agriCropType').value;
    const calcNDVI = document.getElementById('agriCalculateNDVI').checked;
    const calcNDWI = document.getElementById('agriCalculateNDWI').checked;
    
    if (isNaN(lat) || isNaN(lon)) {
        showToast('Please enter valid coordinates', 'error');
        return;
    }
    
    showLoading();
    addLog('Starting agriculture analysis...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/detect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat,
                lon,
                use_gee: false,
                use_vit: true,
                use_ensemble: true,
                detect_clouds: true,
                apply_atmospheric_correction: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            hideLoading();
            addLog(`Agriculture analysis complete. Anomalies: ${data.anomaly_count}`);
            
            // Update vegetation indices
            document.getElementById('ndviValue').textContent = data.ndvi || 'N/A';
            document.getElementById('ndwiValue').textContent = data.ndwi || 'N/A';
            
            // Determine health status
            let healthStatus = 'Unknown';
            if (data.ndvi) {
                if (data.ndvi > 0.6) healthStatus = 'Healthy';
                else if (data.ndvi > 0.3) healthStatus = 'Moderate';
                else healthStatus = 'Stressed';
            }
            document.getElementById('healthStatus').textContent = healthStatus;
            
            // Update agriculture map with detection results
            if (agriMap) {
                // Clear existing markers
                agriMap.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        agriMap.removeLayer(layer);
                    }
                });
                
                // Add marker at detection location
                const marker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: '<div style="background: #39FF14; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
                        iconSize: [20, 20]
                    })
                }).addTo(agriMap);
                
                marker.bindPopup(`
                    <b>Agriculture Analysis</b><br>
                    Crop Type: ${cropType}<br>
                    Health: ${healthStatus}<br>
                    NDVI: ${data.ndvi || 'N/A'}<br>
                    NDWI: ${data.ndwi || 'N/A'}
                `);
                
                // Center map on detection
                agriMap.setView([lat, lon], 15);
            }
            
            showToast('Agriculture analysis complete', 'success');
        } else {
            throw new Error(data.detail || 'Analysis failed');
        }
    } catch (error) {
        hideLoading();
        console.error('Agriculture analysis error:', error);
        showToast('Agriculture analysis failed: ' + error.message, 'error');
    }
}

// Geological Detection Handler
async function runGeoDetection() {
    console.log('Running Geological survey...');
    
    const lat = parseFloat(document.getElementById('geoLatitude').value);
    const lon = parseFloat(document.getElementById('geoLongitude').value);
    const mineralType = document.getElementById('geoMineralType').value;
    const useSAR = document.getElementById('geoUseSAR').checked;
    const useTemporal = document.getElementById('geoTemporal').checked;
    
    if (isNaN(lat) || isNaN(lon)) {
        showToast('Please enter valid coordinates', 'error');
        return;
    }
    
    showLoading();
    addLog('Starting geological survey...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/detect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat,
                lon,
                use_gee: false,
                use_vit: true,
                use_ensemble: true,
                detect_clouds: true,
                apply_atmospheric_correction: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            hideLoading();
            addLog(`Geological survey complete. Anomalies: ${data.anomaly_count}`);
            addLog(`Material identified: ${data.material_identified || 'N/A'}`);
            
            // Display results
            const resultsDiv = document.getElementById('geoResults');
            resultsDiv.innerHTML = `
                <div class="result-item">
                    <label>Mineral Type:</label>
                    <span>${mineralType}</span>
                </div>
                <div class="result-item">
                    <label>Deposits Found:</label>
                    <span>${data.anomaly_count}</span>
                </div>
                <div class="result-item">
                    <label>Material:</label>
                    <span>${data.material_identified || 'Unknown'}</span>
                </div>
                <div class="result-item">
                    <label>Confidence:</label>
                    <span>${(1 - data.fused_threshold).toFixed(2)}</span>
                </div>
            `;
            
            // Update geological map with detection results
            if (geoMap) {
                // Clear existing markers
                geoMap.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        geoMap.removeLayer(layer);
                    }
                });
                
                // Add marker at detection location
                const marker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: '<div style="background: #BC13FE; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
                        iconSize: [20, 20]
                    })
                }).addTo(geoMap);
                
                marker.bindPopup(`
                    <b>Geological Survey</b><br>
                    Mineral Type: ${mineralType}<br>
                    Deposits: ${data.anomaly_count}<br>
                    Material: ${data.material_identified || 'Unknown'}
                `);
                
                // Center map on detection
                geoMap.setView([lat, lon], 15);
            }
            
            showToast('Geological survey complete', 'success');
        } else {
            throw new Error(data.detail || 'Survey failed');
        }
    } catch (error) {
        hideLoading();
        console.error('Geological survey error:', error);
        showToast('Geological survey failed: ' + error.message, 'error');
    }
}

// Event listeners for domain-specific detection buttons
document.addEventListener('DOMContentLoaded', () => {
    // Don't initialize maps on DOM load - they're hidden
    // Maps will initialize when their pages become visible
    
    // Defense detection button
    const defenseBtn = document.getElementById('defenseDetectBtn');
    if (defenseBtn) {
        defenseBtn.addEventListener('click', runDefenseDetection);
    }
    
    // Agriculture detection button
    const agriBtn = document.getElementById('agriDetectBtn');
    if (agriBtn) {
        agriBtn.addEventListener('click', runAgriDetection);
    }
    
    // Geological detection button
    const geoBtn = document.getElementById('geoDetectBtn');
    if (geoBtn) {
        geoBtn.addEventListener('click', runGeoDetection);
    }
    
    // Defense sensitivity slider
    const defenseSensitivity = document.getElementById('defenseSensitivity');
    const defenseSensitivityValue = document.getElementById('defenseSensitivityValue');
    if (defenseSensitivity && defenseSensitivityValue) {
        defenseSensitivity.addEventListener('input', (e) => {
            defenseSensitivityValue.textContent = e.target.value;
        });
    }
    
    // Defense location button
    const defenseLocationBtn = document.getElementById('defenseGetLocationBtn');
    if (defenseLocationBtn) {
        defenseLocationBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                showToast('Geolocation is not supported by your browser', 'error');
                return;
            }
            
            showToast('Getting your location...', 'info');
            defenseLocationBtn.disabled = true;
            defenseLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    document.getElementById('defenseLatitude').value = lat.toFixed(6);
                    document.getElementById('defenseLongitude').value = lon.toFixed(6);
                    
                    if (defenseMap) {
                        defenseMap.setView([lat, lon], 13);
                    }
                    
                    showToast(`Location found: ${lat.toFixed(4)}, ${lon.toFixed(4)}`, 'success');
                    defenseLocationBtn.disabled = false;
                    defenseLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get Current Location';
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    showToast('Failed to get location: ' + error.message, 'error');
                    defenseLocationBtn.disabled = false;
                    defenseLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get Current Location';
                }
            );
        });
    }
    
    // Agriculture location button
    const agriLocationBtn = document.getElementById('agriGetLocationBtn');
    if (agriLocationBtn) {
        agriLocationBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                showToast('Geolocation is not supported by your browser', 'error');
                return;
            }
            
            showToast('Getting your location...', 'info');
            agriLocationBtn.disabled = true;
            agriLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    document.getElementById('agriLatitude').value = lat.toFixed(6);
                    document.getElementById('agriLongitude').value = lon.toFixed(6);
                    
                    if (agriMap) {
                        agriMap.setView([lat, lon], 13);
                    }
                    
                    showToast(`Location found: ${lat.toFixed(4)}, ${lon.toFixed(4)}`, 'success');
                    agriLocationBtn.disabled = false;
                    agriLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get Current Location';
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    showToast('Failed to get location: ' + error.message, 'error');
                    agriLocationBtn.disabled = false;
                    agriLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get Current Location';
                }
            );
        });
    }
    
    // Geological location button
    const geoLocationBtn = document.getElementById('geoGetLocationBtn');
    if (geoLocationBtn) {
        geoLocationBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                showToast('Geolocation is not supported by your browser', 'error');
                return;
            }
            
            showToast('Getting your location...', 'info');
            geoLocationBtn.disabled = true;
            geoLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    document.getElementById('geoLatitude').value = lat.toFixed(6);
                    document.getElementById('geoLongitude').value = lon.toFixed(6);
                    
                    if (geoMap) {
                        geoMap.setView([lat, lon], 13);
                    }
                    
                    showToast(`Location found: ${lat.toFixed(4)}, ${lon.toFixed(4)}`, 'success');
                    geoLocationBtn.disabled = false;
                    geoLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get Current Location';
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    showToast('Failed to get location: ' + error.message, 'error');
                    geoLocationBtn.disabled = false;
                    geoLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get Current Location';
                }
            );
        });
    }
});

// Window resize handler
window.addEventListener('resize', () => {
    // No globe resize needed
});

// Custom Cursor
function initializeCustomCursor() {
    const cursor = document.getElementById('customCursor');
    const trail = document.getElementById('cursorTrail');
    
    if (!cursor || !trail) return;
    
    let trailX = 0, trailY = 0;
    
    // Update cursor position instantly on mousemove
    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX;
        const mouseY = e.clientY;
        
        // Main cursor - instant, centered
        cursor.style.left = (mouseX - 10) + 'px';
        cursor.style.top = (mouseY - 10) + 'px';
    });
    
    // Animate trail with smooth following
    function animateTrail() {
        const mouseX = parseFloat(cursor.style.left) + 10 || 0;
        const mouseY = parseFloat(cursor.style.top) + 10 || 0;
        
        const targetTrailX = mouseX - 4;
        const targetTrailY = mouseY - 4;
        
        trailX += (targetTrailX - trailX) * 0.3;
        trailY += (targetTrailY - trailY) * 0.3;
        
        trail.style.left = trailX + 'px';
        trail.style.top = trailY + 'px';
        
        requestAnimationFrame(animateTrail);
    }
    
    animateTrail();
    
    // Hover effect on interactive elements
    const interactiveElements = document.querySelectorAll('button, a, input, .nav-btn, .tab-btn, .location-btn');
    
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.classList.add('hover');
        });
        
        el.addEventListener('mouseleave', () => {
            cursor.classList.remove('hover');
        });
    });
    
    // Hide default cursor on desktop
    if (window.matchMedia('(pointer: fine)').matches) {
        document.body.style.cursor = 'none';
    }
}
