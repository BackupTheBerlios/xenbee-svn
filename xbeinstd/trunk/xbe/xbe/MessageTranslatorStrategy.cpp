#include "MessageTranslatorStrategy.hpp"

#include "event/ObjectEvent.hpp"
#include "event/XbeInstdEvent.hpp"
#include "event/ExecuteAckEvent.hpp"
#include "event/ExecuteEvent.hpp"
#include "event/FailedAckEvent.hpp"
#include "event/FailedEvent.hpp"
#include "event/FinishedAckEvent.hpp"
#include "event/FinishedEvent.hpp"
#include "event/LifeSignEvent.hpp"
#include "event/ShutdownAckEvent.hpp"
#include "event/ShutdownEvent.hpp"
#include "event/StatusEvent.hpp"
#include "event/StatusReqEvent.hpp"
#include "event/TerminateAckEvent.hpp"
#include "event/TerminateEvent.hpp"

#include "xbe-msg.hpp"

#include <iostream>

using namespace xbe;
using namespace xbe::event;
namespace fs = boost::filesystem;

MessageTranslatorStrategy::MessageTranslatorStrategy(const std::string& name,
        const seda::Strategy::Ptr& decorated)
: seda::StrategyDecorator(name, decorated),
    XBE_INIT_LOGGER(name)
{} 

void MessageTranslatorStrategy::perform(const seda::IEvent::Ptr& e) {
    if (xbe::event::ObjectEvent<xbemsg::message_t> *oe = (dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(e.get()))) {
        using namespace xercesc;

        // extract the body element and transform it into an internal
        // event
        std::auto_ptr<xbemsg::message_t> msg(oe->object());

        const std::string to(msg->header().to());
        const std::string from(msg->header().from());
        const std::string convID(msg->header().conversation_id());            

        if (msg->body().execute()) {
            XBE_LOG_INFO("translating execute");
            xbe::event::ExecuteEvent *evt(new xbe::event::ExecuteEvent(to, from, convID));

            // parse the jsdl description
            if (msg->body().execute()->task()) {
                xbemsg::execute_t::task_type &task(*msg->body().execute()->task()); 
                // keep a mapping for FileSystem definitions
                std::map<std::string, std::string> fsMap;
                // parse the resources (filesystem identifications)
                if (task.Resources()) {
                    for (jsdl::Resources_Type::FileSystem_const_iterator fs = task.Resources()->FileSystem().begin(); fs != task.Resources()->FileSystem().end(); fs++) {
                        if (fs->MountPoint())
                            fsMap[fs->name()] = *fs->MountPoint();
                    }
                }
                if (task.Application()) {
                    // parse a POSIXApplication if possible
                    for (jsdl::Application_Type::any_const_iterator elem(task.Application()->any().begin()); elem!=task.Application()->any().end(); elem++) {
                        std::string name(xsd::cxx::xml::transcode<char>(elem->getLocalName()));
                        if (name != "POSIXApplication") continue;

                        jsdlPosix::POSIXApplication_Type app(*elem);
                        if (app.Executable()) {
                            fs::path executable;
                            if (app.Executable()->filesystemName())
                                executable = fs::path(fsMap[*app.Executable()->filesystemName()]);
                            executable /= *app.Executable();

                            TaskData tData(executable);

                            // parse arguments
                            for (jsdlPosix::POSIXApplication_Type::Argument_const_iterator arg = app.Argument().begin();
                                    arg != app.Argument().end();
                                    arg++) {
                                if (arg->filesystemName()) {
                                    tData.params().push_back((fs::path(fsMap[*arg->filesystemName()]) / fs::path(*arg)).string());
                                } else {
                                    tData.params().push_back(*arg);
                                }
                            }

                            // working directory
                            if (app.WorkingDirectory()) {
                                std::string prefix(app.WorkingDirectory()->filesystemName() ? fsMap[*app.WorkingDirectory()->filesystemName()] : "");
                                tData.wd(fs::path(prefix) / fs::path(*app.WorkingDirectory()));
                            }

                            // redirections
                            if (app.Input()) {
                                std::string prefix(app.Input()->filesystemName() ? fsMap[*app.Input()->filesystemName()] : "");
                                tData.stdIn(fs::path(prefix) / fs::path(*app.Input()));
                            }
                            if (app.Output()) {
                                std::string prefix(app.Output()->filesystemName() ? fsMap[*app.Output()->filesystemName()] : "");
                                tData.stdOut(fs::path(prefix) / fs::path(*app.Output()));
                            }
                            if (app.Error()) {
                                std::string prefix(app.Error()->filesystemName() ? fsMap[*app.Error()->filesystemName()] : "");
                                tData.stdErr(fs::path(prefix) / fs::path(*app.Error()));
                            }

                            // environment
                            for (jsdlPosix::POSIXApplication_Type::Environment_const_iterator env(app.Environment().begin());
                                    env != app.Environment().end();
                                    env++) {
                                std::string val(*env);
                                if (env->filesystemName()) {
                                    val = (fs::path(fsMap[*env->filesystemName()]) / val).string();
                                }
                                tData.env()[env->name()] = val;
                            }

                            // user, group

                            evt->taskData(tData);
                        } else {
                            continue;
                        }
                    }
                }
            }

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().terminate()) {
            XBE_LOG_INFO("translating terminate");
            xbe::event::TerminateEvent *evt(new xbe::event::TerminateEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().status_req()) {
            XBE_LOG_INFO("translating status-req");
            xbe::event::StatusReqEvent *evt(new xbe::event::StatusReqEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().shutdown()) {
            XBE_LOG_INFO("translating shutdown");
            xbe::event::ShutdownEvent *evt(new xbe::event::ShutdownEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().finished_ack()) {
            XBE_LOG_INFO("translating finished-ack");
            xbe::event::FinishedAckEvent *evt(new xbe::event::FinishedAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().failed_ack()) {
            XBE_LOG_INFO("translating failed-ack");
            xbe::event::FailedAckEvent *evt(new xbe::event::FailedAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().life_sign()) {
            XBE_LOG_INFO("translating life-sign");
            xbe::event::LifeSignEvent *evt(new xbe::event::LifeSignEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().execute_ack()) {
            XBE_LOG_INFO("translating execute-ack");
            xbe::event::ExecuteAckEvent *evt(new xbe::event::ExecuteAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().terminate_ack()) {
            XBE_LOG_INFO("translating terminate-ack");
            xbe::event::TerminateAckEvent *evt(new xbe::event::TerminateAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().shutdown_ack()) {
            XBE_LOG_INFO("translating shutdown-ack");
            xbe::event::ShutdownAckEvent *evt(new xbe::event::ShutdownAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().status()) {
            XBE_LOG_INFO("translating status");
            xbe::event::StatusEvent *evt(new xbe::event::StatusEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().finished()) {
            XBE_LOG_INFO("translating finished");
            xbe::event::FinishedEvent *evt(new xbe::event::FinishedEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().failed()) {
            XBE_LOG_INFO("translating failed");
            xbe::event::FailedEvent *evt(new xbe::event::FailedEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else {
            XBE_LOG_ERROR("got some unknown body element!");
        }
    } else if (xbe::event::XbeInstdEvent *xbeEvent = (dynamic_cast<xbe::event::XbeInstdEvent*>(e.get()))) {
        // got an xbeinstd event, transform it to xml
        const std::string to(xbeEvent->to());
        const std::string from(xbeEvent->from());
        const std::string convID(xbeEvent->conversationID());

        xbemsg::header_t header(to, from);
        header.conversation_id(convID);
        xbemsg::body_t body;

        if (xbe::event::ExecuteEvent *evt = dynamic_cast<xbe::event::ExecuteEvent*>(xbeEvent)) {
        } else if (xbe::event::TerminateEvent *evt = dynamic_cast<xbe::event::TerminateEvent*>(xbeEvent)) {
            xbemsg::terminate_t elem;
            body.terminate(elem);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::StatusReqEvent *evt = dynamic_cast<xbe::event::StatusReqEvent*>(xbeEvent)) {
            xbemsg::status_req_t elem;
            body.status_req(elem);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::ShutdownEvent *evt = dynamic_cast<xbe::event::ShutdownEvent*>(xbeEvent)) {
            xbemsg::shutdown_t elem;
            body.shutdown(elem);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::FinishedAckEvent *evt = dynamic_cast<xbe::event::FinishedAckEvent*>(xbeEvent)) {
            xbemsg::finished_ack_t elem;
            body.finished_ack(elem);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::FailedAckEvent *evt = dynamic_cast<xbe::event::FailedAckEvent*>(xbeEvent)) {
            xbemsg::failed_ack_t elem;
            body.failed_ack(elem);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::LifeSignEvent *evt = dynamic_cast<xbe::event::LifeSignEvent*>(xbeEvent)) {
            xbemsg::life_sign_t life_sign;
            body.life_sign(life_sign);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::ExecuteAckEvent *evt = dynamic_cast<xbe::event::ExecuteAckEvent*>(xbeEvent)) {
            xbemsg::execute_ack_t exec_ack;
            body.execute_ack(exec_ack);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::TerminateAckEvent *evt = dynamic_cast<xbe::event::TerminateAckEvent*>(xbeEvent)) {
            xbemsg::terminate_ack_t term_ack;
            body.terminate_ack(term_ack);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::ShutdownAckEvent *evt = dynamic_cast<xbe::event::ShutdownAckEvent*>(xbeEvent)) {
            xbemsg::shutdown_ack_t shutdown_ack;
            body.shutdown_ack(shutdown_ack);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::StatusEvent *evt = dynamic_cast<xbe::event::StatusEvent*>(xbeEvent)) {
            xbemsg::status_t status;
            body.status(status);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::FinishedEvent *evt = dynamic_cast<xbe::event::FinishedEvent*>(xbeEvent)) {
            xbemsg::finished_t finished;
            body.finished(finished);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else if (xbe::event::FailedEvent *evt = dynamic_cast<xbe::event::FailedEvent*>(xbeEvent)) {
            xbemsg::failed_t failed;
            body.failed(failed);

            std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));
            seda::StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::ObjectEvent<xbemsg::message_t>(to, from, msg)));
        } else {
            XBE_LOG_ERROR("got an xbeinstd event: " << e->str());
        }
    } else {
        XBE_LOG_WARN("got some unknown event: " << e->str());
    }
}

