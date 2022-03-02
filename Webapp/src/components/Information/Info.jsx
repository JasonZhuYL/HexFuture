import React, { Component } from "react"
import "./Info.css"
import { LineChart, Line, CartesianGrid, XAxis, YAxis } from 'recharts';

export default class Info extends Component {
  constructor(props) {
    super(props)
    this.state = {
      type: -1
    }
    this.changeType = this.changeType.bind(this)
    this.handleSubmit = this.handleSubmit.bind(this)
    this.sendCommand = this.sendCommand.bind(this)
  }

  changeType = (event) => {
    const type = parseInt(event.target.value)
    console.log(type)
    this.setState({ type })
    console.log(this.state)
    this.handleSubmit()
  }

  handleSubmit = (event) => {
    //event.preventDefault()
    const type = this.state
    if (type !== -1) {
      let type_ready = { type: type }
      this.sendCommand(type_ready)
      console.log(type_ready)
    } else {
      //console.err("unknown submission")
    }
  }

  sendCommand = (command) => {
    fetch('http://18.134.242.125:8000' + "/" + 'type', {
      method: "POST",
      body: JSON.stringify(command),
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((res) => res.json())
      .then(
        (result) => {
          console.log(result)
        },
        // Note: it's important to handle errors here
        // instead of a catch() block so that we don't swallow
        // exceptions from actual bugs in components.
        (error) => {
          console.warn(error)
        }
      )
  }



  render() {
    let { humidityValue,isServerConnected,isPotConnected,humidity, tempurature,lightness,weight,rHumidity,motor,waterpump1,waterpump2} = this.props
    return (
      <table className="pad info">
        <thead>
          <tr>
            <th colSpan="2"><font color='white'>Connection State</font></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Server:</td>
            <td>{isServerConnected ? "connected" : "disconnected"}</td>
          </tr>
          <tr>
            <td>Pot:</td>
            <td>{isPotConnected ? "connected" : "disconnected"}</td>
          </tr>
        </tbody>

        <thead>          
          <tr>
            <th colSpan="2"><font color='white'>Plant Type</font></th>
          </tr></thead>
        <tbody>
        <tr>
            <td>Type:&nbsp;</td>
            <td>
                <select name="type" onChange={this.changeType} width={60} height={30} className='selectbar'>
                    <option value="0">Tête à tête</option>
                    <option value="1">Alstroemerias</option>
                    <option value="2">Aster</option>
                    <option value="3">Calla Lilies</option>
                    <option value="4">Dahlias</option>
                    <option value="5">Daisies</option>
                    <option value="6">Daffodil</option>
                    <option value="7">Delphinium</option>
                    <option value="8">Gerbera Daisies</option>
                    <option value="9">Lavender</option>
                    <option value="10">Lilies</option>
                    <option value="11">Marigold</option>
                    <option value="12">Peonies</option>
                    <option value="13">More to come</option>
                </select>
            </td>
          </tr>
        </tbody>
        <thead>
          <tr>
            <th colSpan="2"><font color='white'>Pot Sensor Reading</font></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Dirt humidity:</td>
            <td>{humidity}</td>
          </tr>
          <tr>
            <td>Air Tempurature:</td>
            <td>{tempurature}</td>
          </tr>
          
          <tr>
            <td>Air Humidity:</td>
            <td>{rHumidity}%</td>
          </tr>
          <tr>
            <td>Sunlight Intensity:</td>
            <td>{lightness} lux</td>
          </tr>
          <tr>
            <td>Water Supply:</td>
            <td>{weight}</td>
          </tr>

        </tbody>
        <thead>
          <tr>
            <th colSpan="2"><font color='white'>Utility State</font></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Gear and Motor:</td>
            <td>{motor ? "Operating" : "Stopped"}</td>
          </tr>
          <tr>
            <td>Water Pump:</td>
            <td>{waterpump1 ? "Operating" : "Stopped"}</td>
          </tr>
        </tbody>
        <thead>
          <tr>
            <th colSpan="2"><font color='white'>Real-time Dirt Humidity / %</font></th>
          </tr>
        </thead>
        <thead>
          <tr className='chart'>
          <LineChart width={700} height={500} data={humidityValue} background="white">
            <Line type="monotone" dataKey="uv" stroke="#000000" strokeWidth={3}/>
            <CartesianGrid stroke="#ccc" /> 
            <XAxis dataKey="name" />
            <YAxis/>
          </LineChart>
          </tr>
        </thead>

      </table>
      
    )
  }
}
