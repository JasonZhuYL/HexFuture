import React,{ Component } from "react"
import Info from "./components/Information/Info"
import "./App.css"


export default class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      isServerConnected: false,
      isPotConnected: false,
      humidity:10,
      tempurature:20,
      lightness:0,
      weight:0,
      rHumidity:0,
      speaker:0,
      motor:0,
      waterpump1:0,
      waterpump2:0,
      humidityValue:0,
      humidityValue: []

    }
  }

  fetchPotState = () => {
    fetch('http://18.134.242.125:8000'+ "/pot")
      .then((res) => res.json())
      .then((res) => {
        console.log(res)
        const {humidityValue,humidity, tempurature,lightness,weight,rHumidity,speaker,motot,waterpump1,waterpump2,isPotConnected} = res
        this.setState({humidityValue,humidity, tempurature,lightness,weight,rHumidity,speaker,motot,waterpump1,waterpump2,isPotConnected})
      })
  }


  componentDidMount() {
    // check if server is online
    fetch('http://18.134.242.125:8000' + "/check")
      .then((res) => {
        if (res.status == 200) {
          console.log("server is online")
          this.setState({ isServerConnected: true })
        }
      })
      .catch((err) => console.log(err))

    this.fetchPotState()
    const timeInterval = 200
    this.timer = setInterval(() => {
      this.fetchPotState()
    }, timeInterval)
  }

  render() {
    return (
      <div className="bo">
        <h1 className="title">Hex Future</h1>

        
        <div className="row">
          <Info
                humidityValue = {this.state.humidityValue}
                isServerConnected = {this.state.isServerConnected}
                isPotConnected = {this.state.isPotConnected}
                humidity = {this.state.humidity}
                tempurature= {this.state.tempurature}
                lightness= {this.state.lightness}
                weight= {this.state.weight}
                rHumidity= {this.state.rHumidity}
                speaker= {this.state.speaker}
                motor= {this.state.motor}
                waterpump1= {this.state.waterpump1}
                waterpump2= {this.state.waterpump2}
          />
        </div>
        <div className="bottom">@2022 Imperial College London EEE/EIE HexFuture</div>
      </div>
    )
  }
}

