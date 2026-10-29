"""Explicit, idempotent fictional demo seed: python -m app.seed."""
from sqlalchemy import select, func
from .main import Base, engine, SessionLocal, Project, log

TOPICS = [
('Water Quality Sensor Network','water quality, sensors, pollution','Monitor river water quality using low-cost sensors, tracking pH and turbidity to identify pollution events.'),
('Crop Disease Image Classifier','agriculture, computer vision, crops','Classify leaf photographs to identify crop diseases and support early intervention for small farms.'),
('Solar Microgrid Forecasting','solar, energy, forecasting','Forecast solar energy production and local electricity demand to improve microgrid battery scheduling.'),
('Flood Risk Mapping','flood, geospatial, rainfall','Combine rainfall observations and terrain maps to identify flood risk and prioritize evacuation planning.'),
('Research Document Retrieval','documents, retrieval, NLP','Index research documents with natural language processing to retrieve relevant records for investigators.'),
('Road Surface Inspection','roads, computer vision, maintenance','Detect potholes from road images and prioritize surface maintenance using estimated damage severity.'),
('Air Pollution Forecasting','air quality, pollution, forecasting','Predict particulate air pollution using weather observations and urban monitoring station measurements.'),
('Smart Irrigation Scheduler','irrigation, agriculture, sensors','Use soil moisture sensors and weather forecasts to schedule irrigation and reduce farm water consumption.'),
('Accessible Campus Navigation','accessibility, navigation, campus','Map accessible campus routes and provide navigation instructions for people with reduced mobility.'),
('Hospital Queue Simulation','hospital, queues, simulation','Simulate outpatient hospital queues to compare appointment schedules and reduce patient waiting times.'),
('Wildlife Acoustic Monitoring','wildlife, audio, classification','Identify bird species from field audio recordings to support wildlife habitat monitoring.'),
('Waste Collection Routing','waste, routing, optimization','Optimize municipal waste collection routes using bin capacity reports and vehicle travel constraints.'),
('Bridge Vibration Analysis','bridges, vibration, sensors','Analyze bridge vibration sensor measurements to flag changes requiring structural engineering inspection.'),
('Local Language Speech Transcription','speech, language, transcription','Evaluate speech transcription for regional language recordings across noisy field conditions.'),
('Warehouse Inventory Forecasting','inventory, warehouse, forecasting','Forecast warehouse item demand from historical transactions to reduce stock shortages.'),
('Emergency Resource Allocation','emergency, allocation, optimization','Compare emergency resource allocation strategies across simulated incident locations and response times.'),
('Groundwater Level Trends','groundwater, water, forecasting','Study groundwater level measurements to estimate seasonal depletion and support conservation planning.'),
('Learning Resource Recommendation','education, recommendations, learning','Recommend learning resources using topic interests and prior course completion records.'),
('Building Energy Audit','buildings, energy, efficiency','Analyze building electricity use to identify opportunities for energy efficiency improvements.'),
('Public Transport Reliability','transport, buses, reliability','Measure bus arrival reliability and compare timetable adjustments using historical journey records.'),
('Food Storage Temperature Alerts','food, temperature, sensors','Monitor food storage temperatures with sensors and record alerts for cold chain interruptions.'),
('Urban Heat Island Mapping','urban, heat, geospatial','Map urban surface temperature patterns to identify heat islands and possible tree planting locations.'),
('Phishing Message Classification','cybersecurity, phishing, NLP','Classify suspicious messages using textual features to support phishing awareness training.'),
('Recycling Material Recognition','recycling, vision, materials','Recognize recyclable material categories from images for a demonstration waste sorting workflow.'),
('Rainwater Harvesting Planner','rainwater, water, planning','Estimate rainwater harvesting capacity from roof area and seasonal rainfall records.'),
('Library Book Recommendation','library, books, recommendations','Recommend library books from subject keywords and borrowing patterns using anonymized sample data.'),
('Industrial Machine Maintenance','machines, maintenance, vibration','Analyze machine vibration and operating hours to flag maintenance inspection priorities.'),
('Disaster Shelter Capacity Tracker','disaster, shelter, capacity','Track shelter capacity and availability in fictional disaster response exercises.'),
('Citizen Feedback Topic Analysis','feedback, NLP, topics','Group citizen feedback by topic to help reviewers identify recurring municipal service concerns.'),
('Research Grant Milestone Tracker','research, grants, milestones','Track grant project milestones, progress notes and reporting deadlines in a shared research register.'),
]

def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Project)):
            print('Database is nonempty; no demo records added.')
            return
        for i,(title,keywords,summary) in enumerate(TOPICS):
            status=['ongoing','completed','planned'][i%3]
            p=Project(title=title,summary=summary,owner=f'Demo Research Team {i+1:02}',keywords=keywords,status=status,completion=100 if status=='completed' else (30 if status=='ongoing' else 0))
            db.add(p); db.flush(); log(db,p,'Demo Seeder','created',{'source':'Fictional demonstration record'})
        db.commit()
        print('Created 30 fictional projects: 10 ongoing, 10 completed, 10 planned.')

if __name__=='__main__': seed()
