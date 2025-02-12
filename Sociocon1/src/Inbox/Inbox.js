import React, {useState} from "react"
import Sidebar from '../Sidebar'
import News from '../News'
import {NavLink, Routes, Route, Outlet } from "react-router-dom"
//import "./Style.css";
import "./styles/Inbox.css"
import ActivityTab from "./ActivityTab";
import FriendRequestsTab from "./FriendRequestsTab";
import MessagesTab from "./MessagesTab";
import TabDesc from "./TabDesc";
import Tabs from "./Tabs";
import RemPosts from "./RemPosts"

// const tabList = [
//     {
//       id: 'all',
//       label: 'All',
//     },
//     {
//       id: 'mentions',
//       label: 'Mentions',
//     },
//   ]

export default function Inbox() {
    //initial selected tab will be activity
    const [currentTab, setCurrentTab] = useState("requests");
    const preferredName = localStorage.getItem("preferredName")
    
    // Handle when user changes tabs
    function handleActivityTab() {
        setCurrentTab("activity")
    }

    function handleRequestsTab() {
        setCurrentTab("requests")
    }

    function handleMessagesTab() {
        setCurrentTab("messages")
    }

    return (
    <div>
        <Sidebar/>
        
        <div
        
        className="Inbox">
            
            <div className="InboxHeader">
                <h1>Inbox</h1>
                <h3>User: {preferredName}</h3>
            </div>
            <ul className="choose">
                <TabDesc id="activity" title="Activity" currentTab={currentTab} setCurrentTab={setCurrentTab}/>
                <TabDesc id="requests" title="Friend Requests" currentTab={currentTab} setCurrentTab={setCurrentTab}/>
                <TabDesc id="authorlist" title="AuthorList" currentTab={currentTab} setCurrentTab={setCurrentTab}/>
                <TabDesc id="remposts" title="RemPosts" currentTab={currentTab} setCurrentTab={setCurrentTab}/>
                {/* <li className={currentTab === "activity" ? "current" : ""}
                onClick={handleActivityTab}>Activity</li>
                <li className={currentTab === "requests" ? "current" : ""}
                onClick={handleRequestsTab}>Friend Requests</li>
                <li className={currentTab === "messages" ? "current" : ""}
                onClick={handleMessagesTab}>Messages</li> */}
                
            </ul>
            <div className="outlet">
                <Tabs id="activity" currentTab={currentTab}>
                    {/* <p>Activity works</p> */}
                    <ActivityTab />
                </Tabs>
                <Tabs id="requests" currentTab={currentTab}>
                    <FriendRequestsTab />
                </Tabs>
                <Tabs id="authorlist" currentTab={currentTab}>
                    <MessagesTab />
                </Tabs>
                <Tabs id="remposts" currentTab={currentTab}>
                    <RemPosts/>
                </Tabs>
                {/* {currentTab === "activity" ? <ActivityTab /> : ""}
                {currentTab === "requests" ? <FriendRequestsTab /> : ""}
                {currentTab === "messages" ? <MessagesTab /> : ""} */}
            </div>
        </div>
        {/* <News/> */}
    </div>
  )
}